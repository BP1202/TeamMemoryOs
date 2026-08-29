# Knowledge Graph Engine Skill

## Purpose

Build and maintain TeamMemoryOS Knowledge Graph and Hybrid Retrieval architecture.

## Responsibilities

* Entity extraction from engineering memories.
* Knowledge graph node and relationship management.
* Memory linking across projects, PRs, files, incidents, and technologies.
* Hybrid retrieval using vector similarity and graph traversal.
* Explainable retrieval with citation paths.

## Rules

* Prefer deterministic extraction before LLM extraction.
* Keep graph logic inside dedicated services.
* Never bypass organization isolation.
* Keep retrieval explainable and testable.
* Update Sprint 5 engineering journal after each milestone.