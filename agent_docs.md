# DevOps Pipeline Multi-Agent System - Agent Documentation

This document describes the role, inputs, outputs, prompting strategies, and core logic of each agent in the Hindsight-Powered DevOps Pipeline Agent system.

---

## 1. Context Agent

### Purpose & Role
Acts as the entrypoint parser and session manager. It isolates metadata from raw git diffs and indexes the pipeline run into the Hindsight database.

*   **Inputs:** `git_diff`, `metadata` (author, timestamp).
*   **Outputs:** `hindsight_session_id`, `metadata` (adds changed file names and classified categories).
*   **Logic:**
    *   Parses the raw unified git diff using a regular expression to extract paths of modified/added files.
    *   Classifies changes into `cloud_infra` (Terraform/Docker/Kubernetes), `git_meta` (`.gitignore`/CI-CD YAMLs), or `app_code` (application sources).
    *   Saves the session with the metadata to `database.json`/`sessions_index.jsonl`.
    *   Ensures `loop_count` is tracked for reflection loops.

---

## 2. Reviewer V1 (Heuristic Triage)

### Purpose & Role
Performs fast, low-cost screening of the incoming diff against the semantic memory (Hindsight DB) of past system incidents. If no correlation is found, the pipeline is cleared instantly.

*   **Inputs:** `git_diff`.
*   **Outputs:** `risk_flag` (boolean), `risk_reason` (string).
*   **Prompting & LLM Strategy:**
    *   Checks if the Hindsight database has entries matching the diff's keywords.
    *   If matches exist, sends the diff and the historical incident text to Groq (`llama3-70b-8192`) with a structured schema.
    *   Asks the LLM to output a JSON payload indicating whether the changes risk repeating the historical failure.

---

## 3. Reviewer V2 (Deep-Dive Planner)

### Purpose & Role
If a risk is identified by V1, V2 designs the query strategy to pull relevant telemetry logs and documentation. It prepares the "research case" for specialized agents.

*   **Inputs:** `git_diff`, `risk_reason`.
*   **Outputs:** `retrieval_queries` (list of strings).
*   **Prompting & LLM Strategy:**
    *   Instructs the LLM to formulate 2 to 4 precise search queries targeting historical issue boards, code repositories, or telemetry systems (e.g. AWS CloudWatch, Datadog).
    *   Uses a strict JSON schema return containing `retrieval_queries`.

---

## 4. Retrieval Agent

### Purpose & Role
Acts as the tool-integrator. Simulates calling telemetry APIs, logs pipelines, and incident trackers to retrieve context for the specialist nodes.

*   **Inputs:** `retrieval_queries`.
*   **Outputs:** `retrieved_logs` (list of logs and issue descriptions).
*   **Logic:**
    *   Takes queries from V2 and scans the local database or logs mapping rules to extract relevant, synthetic telemetry events.
    *   Generates realistic, structured logs (such as database socket exhaustion, Terraform open-ingress compliance warnings, or hardcoded credential alerts) that correspond to the queries.

---

## 5. Git Expert (Specialist)

### Purpose & Role
Performs security code reviews on git hygiene, sensitive configuration leakage, and pre-commit security standards.

*   **Inputs:** `git_diff`, `retrieved_logs`.
*   **Outputs:** `agent_analyses['git_expert']` (markdown text).
*   **Prompting & LLM Strategy:**
    *   Instructs the LLM to act as a Git hygiene and secrets scanner.
    *   Flags committed `.env` files, API keys, passwords, database connection strings, or private key patterns (`-----BEGIN PRIVATE KEY-----`).
    *   Outputs findings in Markdown containing a clear summary and suggested git-remediation patches (e.g. adding files to `.gitignore` or using BFG Repo-Cleaner).

---

## 6. Cloud/Infra Expert (Specialist)

### Purpose & Role
Analyzes infrastructure-as-code files to detect cloud configuration risks, security group violations, base-image vulnerabilities, and container configuration errors.

*   **Inputs:** `git_diff`, `retrieved_logs`.
*   **Outputs:** `agent_analyses['cloud_expert']` (markdown text).
*   **Prompting & LLM Strategy:**
    *   Instructs the LLM to act as an SRE and IaC Security Architect.
    *   Evaluates Terraform, Dockerfiles, and YAML configurations.
    *   Flags open security groups (e.g. `0.0.0.0/0` on port 22), missing non-root `USER` declarations in Docker, and unpinned base images (like `node:latest`).
    *   Outputs findings and remediation patches.

---

## 7. Application Code Expert (Specialist)

### Purpose & Role
Reviews application-level codebase changes for performance concerns, connection pool depletion bugs, resource leakages, and injection vulnerabilities.

*   **Inputs:** `git_diff`, `retrieved_logs`.
*   **Outputs:** `agent_analyses['code_expert']` (markdown text).
*   **Prompting & LLM Strategy:**
    *   Instructs the LLM to act as an Elite App Auditor.
    *   Evaluates language-specific source files (Python, JS, TS, etc.).
    *   Flags connection leaks (missing `.close()` or try-finally blocks), memory leaks, and SQL injection patterns.
    *   Outputs detailed code diagnostics and proposed safe patches.

---

## 8. Big Boss (Centralized Orchestrator)

### Purpose & Role
The executive decision-maker. Merges the separate, concurrent reports of the three specialists, resolves contradictions, writes the final audit, and administers the loopback reflection guardrail.

*   **Inputs:** `git_diff`, `agent_analyses`, `loop_count`.
*   **Outputs:** `final_audit` (comprehensive markdown), `metadata` (adds re-review signals).
*   **Prompting & LLM Strategy:**
    *   Synthesizes the three specialist markdown sections.
    *   Determines if there is a glaring discrepancy or conflicting logic. If so, and if `loop_count < 1`, sets `needs_rereview = True` to trigger a corrective pass.
    *   Compiles a final report containing a clear VERDICT (Approved / Blocked), a business risk description, and a unified remediation patch list.
