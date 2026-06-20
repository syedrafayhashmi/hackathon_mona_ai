# Graph Report - hackathon_problems_20260620  (2026-06-20)

## Corpus Check
- 31 files · ~556,339 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 273 nodes · 601 edges · 17 communities (13 shown, 4 thin omitted)
- Extraction: 82% EXTRACTED · 18% INFERRED · 0% AMBIGUOUS · INFERRED: 107 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `83677e23`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]

## God Nodes (most connected - your core abstractions)
1. `AuditEvent` - 34 edges
2. `WorkflowResult` - 20 edges
3. `FileStatus` - 20 edges
4. `AIWorkflowValidationError` - 20 edges
5. `DataTable` - 16 edges
6. `compilerOptions` - 16 edges
7. `AgentTask` - 15 edges
8. `merge_file_results()` - 15 edges
9. `RunRecord` - 14 edges
10. `AgentWorkflowOutput` - 13 edges

## Surprising Connections (you probably didn't know these)
- `RunRecord` --uses--> `GeminiUnavailableError`  [INFERRED]
  apps/api/app/main.py → apps/api/app/gemini.py
- `RunRecord` --uses--> `GeminiGenerationError`  [INFERRED]
  apps/api/app/main.py → apps/api/app/gemini.py
- `RunRecord` --uses--> `GeminiRateLimitError`  [INFERRED]
  apps/api/app/main.py → apps/api/app/gemini.py
- `WorkflowState` --uses--> `WorkflowResult`  [INFERRED]
  apps/api/app/graph.py → apps/api/app/models.py
- `WorkflowState` --uses--> `AgentTask`  [INFERRED]
  apps/api/app/graph.py → apps/api/app/workflows.py

## Import Cycles
- 1-file cycle: `apps/api/app/main.py -> apps/api/app/main.py`

## Communities (17 total, 4 thin omitted)

### Community 1 - "Community 1"
Cohesion: 0.08
Nodes (30): CaseSummary, Dashboard(), fallbackModules, iconMap, ModuleWorkspace(), OperationsHub(), statusTone(), valueCell() (+22 more)

### Community 2 - "Community 2"
Cohesion: 0.13
Nodes (29): approve_run(), create_run(), _gather_and_merge(), lifespan(), Fan out one Gemini agent per organizer source file (batch fixtures)., Fan out one Gemini agent per uploaded file, then merge into one batch result., Problem 10 action: send a missing/corrected document request to the applicant., Problem 2 action: message the top-ranked eligible candidate to cover the gap. (+21 more)

### Community 3 - "Community 3"
Cohesion: 0.23
Nodes (24): AgentReview, AgentWorkflowOutput, DataTable, FileStatus, ModuleDefinition, WorkflowResult, AIWorkflowValidationError, merge_file_results() (+16 more)

### Community 4 - "Community 4"
Cohesion: 0.07
Nodes (29): dependencies, class-variance-authority, clsx, lucide-react, next, @radix-ui/react-dialog, @radix-ui/react-dropdown-menu, @radix-ui/react-tabs (+21 more)

### Community 5 - "Community 5"
Cohesion: 0.10
Nodes (19): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+11 more)

### Community 6 - "Community 6"
Cohesion: 0.33
Nodes (15): AgentTask, _build_graph(), _get_graph(), node_intake(), node_review(), node_security(), node_solve(), node_validate() (+7 more)

### Community 7 - "Community 7"
Cohesion: 0.10
Nodes (32): extract_text(), AgentTask, build_agent_task(), build_single_file_task(), build_single_upload_task(), _create_artifacts(), execute_workflow(), _ffmpeg_escape() (+24 more)

### Community 8 - "Community 8"
Cohesion: 0.25
Nodes (7): Demo / pitch mode, Development, Gemini agent architecture, Mona AI Enterprise Operations Hub, Parallel batch processing, Rate-limit visibility (Docker logs), Run locally with Docker

### Community 9 - "Community 9"
Cohesion: 0.29
Nodes (5): 1. Think Before Coding, 2. Simplicity First, 3. Surgical Changes, 4. Goal-Driven Execution, graphify

### Community 15 - "Community 15"
Cohesion: 0.12
Nodes (22): _backoff_delay(), _extract_json(), GeminiAdapter, GeminiGenerationError, GeminiRateLimitError, GeminiUnavailableError, _is_rate_limit(), Run one structured Gemini call with logging and bounded exponential backoff retr (+14 more)

## Knowledge Gaps
- **65 isolated node(s):** `Any`, `metadata`, `iconMap`, `fallbackModules`, `CaseSummary` (+60 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AuditEvent` connect `Community 6` to `Community 2`, `Community 3`, `Community 15`, `Community 7`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **Why does `execute_workflow()` connect `Community 7` to `Community 2`, `Community 6`?**
  _High betweenness centrality (0.012) - this node is a cross-community bridge._
- **Why does `RunRecord` connect `Community 2` to `Community 3`, `Community 15`?**
  _High betweenness centrality (0.011) - this node is a cross-community bridge._
- **Are the 18 inferred relationships involving `AuditEvent` (e.g. with `AgentTask` and `WorkflowState`) actually correct?**
  _`AuditEvent` has 18 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `WorkflowResult` (e.g. with `AgentTask` and `WorkflowState`) actually correct?**
  _`WorkflowResult` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `FileStatus` (e.g. with `AgentTask` and `AIWorkflowValidationError`) actually correct?**
  _`FileStatus` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 11 inferred relationships involving `AIWorkflowValidationError` (e.g. with `AgentWorkflowOutput` and `AuditEvent`) actually correct?**
  _`AIWorkflowValidationError` has 11 INFERRED edges - model-reasoned connections that need verification._