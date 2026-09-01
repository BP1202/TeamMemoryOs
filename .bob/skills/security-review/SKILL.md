# Security Review Skill

## Purpose

Perform a lightweight security audit after every completed backend feature.

## Checklist

* Input validation uses Pydantic.
* SQLAlchemy ORM is used safely.
* No plaintext passwords or secrets.
* Environment variables store credentials.
* Sensitive data is not returned in API responses.
* Logs do not expose secrets.
* Organization data remains isolated.

## Risk Levels

* Low — No new security exposure.
* Medium — Authentication or authorization affected.
* High — Secrets, permissions, or tenant isolation impacted.

## Output

Security Audit

* Input Validation: ✅
* Secrets Exposure: None
* Authorization Impact: Low / Medium / High
* Sensitive Logging: None
* Risk Level: Low