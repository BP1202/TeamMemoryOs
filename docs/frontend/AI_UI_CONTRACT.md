# AI UI Contract

Every AI-generated response in TeamMemoryOS must render these sections.

## Mandatory

* Answer
* Citations
* Confidence Score
* Retrieval Mode
* Graph Path
* Participating Agents
* Suggested Actions

## Never Hide

These sections are visible by default.

## Source of Truth

Data comes from backend explainability APIs only.

Frontend never fabricates citations or confidence values.

## Reused By

* AI Chat
* Retrieval Inspector
* Engineering Copilot
* Multi-Agent Workspace
* AI Governance Dashboard