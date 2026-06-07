# Backend Module Reference

This document provides a concise overview of the files and modules inside the `Backend/` folder, their purpose, and the primary interfaces to use when working with the repository.

---

**Repository Root Files**

- **.env.example**: Environment variable template. Copy to `.env` and populate `GROQ_API_KEY` and optionally `GROQ_MODEL`.
- **.gitignore**: Standard git ignore rules for the project.
- **requirements.txt**: Python package dependencies required by the project.
- **database.json**: Local JSON-based Hindsight database containing historical incidents used by the pipeline.
- **README.md**: Project setup and architecture overview. See this file for quick start instructions.
- **agent_docs.md**: Detailed agent-level specifications and prompting strategies for each agent in the `agents/` package.
- **synthetic_data_flow.md**: Notes and design for synthetic telemetry and data-flow used in tests and retrieval simulation.

---

**Core Python Modules**

- **hindsight_db.py**
  - Purpose: Implements `HindsightDB` — a lightweight local incident store and simple keyword matcher used to simulate the historical memory layer.
  - Key methods: `query_incidents(query_text, limit)`, `save_session(session_id, git_diff, metadata)`, `get_all_incidents()`.
  - Usage: Instantiate via `from hindsight_db import HindsightDB` or use `agents.utils.get_db()`.

- **state.py**
  - Purpose: Defines the `SharedGraphState` TypedDict describing pipeline state and `merge_analyses` reducer used during the parallel fan-in.
  - Key items: `SharedGraphState` fields (e.g., `git_diff`, `agent_analyses`, `loop_count`, `final_audit`).

- **graph.py**
  - Purpose: Constructs the LangGraph `StateGraph` workflow, registers nodes (agents), edges, conditional routers, and compiles the pipeline (`app`).
  - Key functions: `increment_loop(state)` and conditional routers `route_post_v1` and `route_post_big_boss`.
  - Usage: Import `app` and call `app.invoke(inputs)` to run the pipeline with an input state (see `test_pipeline.py`).

- **test_pipeline.py**
  - Purpose: Interactive test harness with synthetic diffs to exercise the pipeline scenarios (safe, risky infra, risky code).
  - Usage: Run `python test_pipeline.py` after setting `GROQ_API_KEY` in `.env` to exercise scenarios.


---

**Agents Package (Backend/agents/)**

All agents expect and return pieces of the `SharedGraphState`. They use `agents.utils.get_llm()` and `agents.utils.get_db()` for shared dependencies.

- **__init__.py**: Package initializer.

- **utils.py**
  - Purpose: Small helpers to return a configured LLM client (`get_llm()`) and a `HindsightDB` instance (`get_db()`).

- **context_agent.py**
  - Purpose: Entrypoint agent that parses `git_diff`, extracts changed file paths, classifies files into categories, generates a `hindsight_session_id`, and indexes the session via `HindsightDB.save_session()`.
  - Outputs: `hindsight_session_id`, `metadata`, `loop_count`.

- **reviewer_v1.py**
  - Purpose: Fast heuristic triage that queries the Hindsight DB for matching historical incidents and (optionally) asks the LLM to verify whether the new diff repeats past failures.
  - Outputs: `risk_flag` (bool) and `risk_reason` (string).

- **reviewer_v2.py**
  - Purpose: When `reviewer_v1` flags risk, V2 formulates 2–4 targeted retrieval queries (logs, PRs, issues) for the `retrieval_agent`.
  - Outputs: `retrieval_queries` (list of strings).

- **retrieval_agent.py**
  - Purpose: Executes/simulates the queries produced by V2: it fetches matching incidents from `HindsightDB` and appends synthesized telemetry entries (e.g., CloudWatch, Trivy, GitSecretGuard) to support specialist agents.
  - Outputs: `retrieved_logs` (list of dicts).

- **git_expert.py**
  - Purpose: Specialist agent that inspects git metadata and code diffs for secrets, `.gitignore` issues, and git hygiene problems.
  - Outputs: `agent_analyses['git_expert']` (Markdown string with findings and remediation suggestions).

- **cloud_expert.py**
  - Purpose: Specialist agent analyzing IaC (Terraform, Docker, K8s YAML) for misconfigurations such as open CIDRs, root containers, or unpinned images.
  - Outputs: `agent_analyses['cloud_expert']` (Markdown string).

- **code_expert.py**
  - Purpose: Specialist agent analyzing application code changes for runtime bugs, connection leaks, SQL injection patterns, and other code-level vulnerabilities.
  - Outputs: `agent_analyses['code_expert']` (Markdown string).

- **big_boss.py**
  - Purpose: Aggregator and decision-maker that synthesizes specialist reports into an executive `final_audit` (Markdown), decides the `needs_rereview` guardrail, and populates metadata to control loopback.
  - Key interface: `big_boss(state) -> dict` returns `final_audit` and updated `metadata` (including `needs_rereview`).


---

**How to Use / Where to Start**

- Quick run: set `GROQ_API_KEY` in `.env` and execute `python test_pipeline.py` to interact with scenarios.
- To programmatically run the pipeline, import `from graph import app` and call `app.invoke(inputs)` where `inputs` conforms to `SharedGraphState`.
- To inspect the Hindsight dataset, open `database.json` and modify or extend incident entries used in tests.

---

**Notes & Next Steps (optional)**

- Consider adding inline module docstrings to each Python file for IDE integration and auto-generated Sphinx docs.
- Add a `docs/` folder and split per-file docs if you need richer documentation or API references.