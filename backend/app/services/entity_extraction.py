"""Deterministic entity extraction from engineering text.

Extracts the following entity types using regular expressions and
heuristics — no LLM required:

* PULL_REQUEST  — PR/MR numbers (e.g. "#123", "PR-123", "!456")
* BRANCH        — Git branch names (e.g. "feat/foo-bar", "fix/issue-42")
* FILE          — File paths with common extensions
* API_ENDPOINT  — HTTP method + path patterns (e.g. "GET /api/v1/users")
* TECHNOLOGY    — Known engineering keywords
* SERVICE       — Capitalised service-style names (e.g. "AuthService")
* REPOSITORY    — Repo-style names (org/repo or snake_case repo names)
"""
import re
from dataclasses import dataclass

from app.models.entity import EntityType


@dataclass(frozen=True)
class RawEntity:
    entity_type: EntityType
    name: str


# ---------------------------------------------------------------------------
# Compiled regex patterns
# ---------------------------------------------------------------------------

_PR_PATTERNS = re.compile(
    r"""
    (?:
        \bPR[- ]?(\d+)\b       # PR-123, PR 123, PR123
        | \bMR[- ]?(\d+)\b     # MR-123 (GitLab style)
        | !\s*(\d+)\b           # !456 (GitLab)
        | \#(\d+)\b             # #123
        | pull\s+request\s+(\d+)  # pull request 99
    )
    """,
    re.VERBOSE | re.IGNORECASE,
)

_BRANCH_PATTERNS = re.compile(
    r"""
    \b(
        (?:feat|fix|chore|refactor|test|docs|hotfix|release|bugfix)
        /[\w.\-/]+
    )\b
    """,
    re.VERBOSE | re.IGNORECASE,
)

_FILE_PATTERNS = re.compile(
    r"""
    \b(
        [\w.\-/]+
        \.(?:py|ts|tsx|js|jsx|go|java|rs|rb|php|cs|cpp|c|h|
             yaml|yml|json|toml|ini|cfg|conf|env|
             md|rst|txt|html|css|scss|
             sql|sh|bash|dockerfile)
    )\b
    """,
    re.VERBOSE | re.IGNORECASE,
)

_API_ENDPOINT_PATTERNS = re.compile(
    r"""
    \b(
        (?:GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)
        \s+
        /[\w.\-/{}:?=&%+]*
    )\b
    """,
    re.VERBOSE | re.IGNORECASE,
)

_REPO_PATTERNS = re.compile(
    r"""
    \b(
        [\w.\-]+/[\w.\-]+          # org/repo
    )\b
    """,
    re.VERBOSE,
)

# Ordered by specificity — longer strings first to avoid substring shadowing.
_KNOWN_TECHNOLOGIES: list[str] = sorted(
    [
        # Languages
        "Python", "TypeScript", "JavaScript", "Go", "Rust", "Java",
        "Kotlin", "Swift", "Ruby", "PHP", "C#", "C++",
        # Frameworks / Libraries
        "FastAPI", "Django", "Flask", "Express", "NestJS", "React", "Vue",
        "Angular", "Next.js", "Nuxt", "Spring Boot", "Rails", "Laravel",
        "SQLAlchemy", "Pydantic", "LangChain",
        # Databases / Data
        "PostgreSQL", "MySQL", "SQLite", "Redis", "MongoDB", "Elasticsearch",
        "Cassandra", "DynamoDB", "Snowflake", "BigQuery", "pgvector",
        # Infrastructure / DevOps
        "Docker", "Kubernetes", "Helm", "Terraform", "Ansible",
        "GitHub Actions", "GitLab CI", "CircleCI", "Jenkins",
        "AWS", "GCP", "Azure", "Heroku", "Vercel", "Netlify",
        # Messaging / Streaming
        "Kafka", "RabbitMQ", "Celery", "gRPC", "GraphQL", "REST",
        "WebSocket", "MQTT",
        # AI / ML
        "OpenAI", "Granite", "LangChain", "Hugging Face", "PyTorch",
        "TensorFlow", "scikit-learn", "pandas", "NumPy",
        # Protocols / Standards
        "OAuth2", "JWT", "OIDC", "SAML", "OpenAPI", "Swagger",
    ],
    key=len,
    reverse=True,
)

# Matches "AuthService", "UserRepository", "PaymentGateway",
# "AuthTokenService" etc.  One or more CamelCase prefix words + suffix.
_SERVICE_NAME_PATTERN = re.compile(
    r"\b([A-Z][a-z]+(?:[A-Z][a-z]+)*"
    r"(?:Service|Repository|Controller|"
    r"Handler|Manager|Provider|Client|Gateway|Adapter|Factory|"
    r"Middleware|Worker|Processor|Resolver))\b"
)


# ---------------------------------------------------------------------------
# Public extraction entry-point
# ---------------------------------------------------------------------------

def extract_entities(text: str) -> list[RawEntity]:
    """Extract engineering entities from *text* deterministically.

    Returns a deduplicated list of :class:`RawEntity` objects sorted by
    entity type then name.  The caller is responsible for persisting them.
    """
    seen: set[tuple[EntityType, str]] = set()
    results: list[RawEntity] = []

    def _add(entity_type: EntityType, raw_name: str) -> None:
        name = _normalise(entity_type, raw_name)
        key = (entity_type, name)
        if key not in seen:
            seen.add(key)
            results.append(RawEntity(entity_type=entity_type, name=name))

    # Pull requests
    for match in _PR_PATTERNS.finditer(text):
        number = next(g for g in match.groups() if g is not None)
        _add(EntityType.PULL_REQUEST, f"PR-{number}")

    # Git branches
    for match in _BRANCH_PATTERNS.finditer(text):
        _add(EntityType.BRANCH, match.group(1))

    # Files
    for match in _FILE_PATTERNS.finditer(text):
        candidate = match.group(1)
        # Skip very short names that are likely noise (e.g. "a.py")
        if len(candidate) >= 4:
            _add(EntityType.FILE, candidate)

    # API endpoints
    for match in _API_ENDPOINT_PATTERNS.finditer(text):
        _add(EntityType.API_ENDPOINT, match.group(1))

    # Technologies (scan using known list to avoid over-matching)
    text_lower = text.lower()
    for tech in _KNOWN_TECHNOLOGIES:
        if tech.lower() in text_lower:
            _add(EntityType.TECHNOLOGY, tech)

    # Service names
    for match in _SERVICE_NAME_PATTERN.finditer(text):
        _add(EntityType.SERVICE, match.group(1))

    # Repositories (org/repo pattern — only when it looks like a real repo)
    for match in _REPO_PATTERNS.finditer(text):
        candidate = match.group(1)
        # Exclude paths that already matched as files or branches
        if "/" in candidate and not _looks_like_path(candidate):
            parts = candidate.split("/")
            if all(part and len(part) >= 2 for part in parts):
                _add(EntityType.REPOSITORY, candidate)

    results.sort(key=lambda e: (e.entity_type.value, e.name))
    return results


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

def _normalise(entity_type: EntityType, name: str) -> str:
    """Normalise an extracted entity name for consistent storage."""
    name = name.strip()
    if entity_type == EntityType.PULL_REQUEST:
        # Ensure canonical PR-NNN format
        digits = re.sub(r"\D", "", name)
        return f"PR-{digits}"
    if entity_type == EntityType.BRANCH:
        return name.lower()
    if entity_type == EntityType.API_ENDPOINT:
        # Normalise method to uppercase
        parts = name.split(None, 1)
        if len(parts) == 2:
            return f"{parts[0].upper()} {parts[1]}"
    if entity_type == EntityType.FILE:
        return name.lower()
    return name


def _looks_like_path(s: str) -> bool:
    """Return True if string resembles a file path (has an extension)."""
    return bool(re.search(r"\.\w{1,6}$", s))
