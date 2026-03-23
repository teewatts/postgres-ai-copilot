# postgres-ai-copilot

AI-assisted PostgreSQL query plan analysis and tuning recommendations.

## Overview

`postgres-ai-copilot` is a local-first tool for analyzing PostgreSQL queries and execution plans.

The project combines:
- deterministic heuristics
- structured LLM reasoning
- evidence-based recommendations
- a path toward live database analysis

## Initial Goal

For v1, the tool accepts:
- a SQL query
- optional schema and index definitions
- an optional `EXPLAIN` or `EXPLAIN ANALYZE` plan

It returns:
- a bottleneck summary
- likely root cause
- estimate mismatch flags
- index recommendations
- rewrite suggestions
- safety notes
- confidence level
- structured JSON output for evaluation

## Why this project

Query tuning is often expert-heavy and time-consuming. PostgreSQL execution plans contain rich signals, but they are not always easy to interpret quickly. This project aims to make that analysis more accessible and repeatable while preserving engineering rigor.

## Planned roadmap

### v1
Offline advisor:
- manual query input
- pasted execution plan
- optional schema and index input
- heuristic + LLM recommendations

### v1.5
Connected mode:
- connect to PostgreSQL
- auto-run `EXPLAIN (FORMAT JSON)`
- auto-fetch relevant schema metadata
- auto-fetch indexes

### v2
Operational analysis:
- workload statistics
- slow-query summaries
- trend detection
- stronger diagnostics

### v3
AI DBA direction:
- supervised remediation drafts
- maintenance advisories
- regression analysis
- human-in-the-loop actions

## Project structure

```text
app/
  api/
  heuristics/
  llm/
  parsers/
  schemas/
  services/
  ui/
tests/
examples/
docs/