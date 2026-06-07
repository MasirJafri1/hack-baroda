# DevOps Deki-Guardrail

A Hindsight-Powered DevOps Pipeline Agent that uses LangGraph, FastAPI, and React/Vite to perform intelligent triage, Specialist Agent analysis, and automated risk analysis for incoming DevOps modifications.

---

## 🎯 The Demo Repository (`11-anos/demo-vulnerable-microservice`)

To showcase the agent's capabilities, we have created a dedicated demonstration repository: [11-anos/demo-vulnerable-microservice](https://github.com/11-anos/demo-vulnerable-microservice).

- **Purpose:** This repository represents a real-world FastAPI microservice.
- **Vulnerability Injection:** Its latest commit contains **5 critical security anti-patterns** mapped exactly to historical incidents in our Hindsight database:
  - **INC-001 (AWS Security Groups):** Open SSH access (`0.0.0.0/0` on port 22) in Terraform configs.
  - **INC-002 (FD Leak):** Unbounded connection pool sizes and unclosed WebSocket handlers.
  - **INC-003 (Secrets Exposure):** Hardcoded production credentials directly in code.
  - **INC-004 (SQL Injection):** Raw string formatting (`f"SELECT..."`) in SQL execution instead of parameterized queries.
  - **INC-005 (Docker Root Execution):** Docker base image set to `python:latest` running as root user.
- **Use Case:** Entering this repository in the Web Dashboard triggers the full specialist escalation workflow, resulting in a **BLOCKED / REQUIRES_REVIEW** verdict.

---

## 🛠️ Quick Start (Local Setup)

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm (Node Package Manager)

### Step 1: Environment Variables Configuration
Configure the `.env` file in the **`Backend/`** directory. It should contain:
```ini
# Groq API Configuration
GROQ_API_KEY="your_groq_api_key"
GROQ_MODEL="llama-3.3-70b-versatile"

# GitHub Token (Required to retrieve commit history/diffs from public/private repos)
GITHUB_TOKEN="your_personal_github_token"

# GitHub Webhook Secret (Optional, used for automating checks via github webhooks)
GITHUB_WEBHOOK_SECRET="your_webhook_secret_here"
```

### Step 2: Automatic Start
At the root of the project, double-click **`run.bat`** (or execute it via PowerShell/CMD):
```powershell
.\run.bat
```
This script will automatically boot the FastAPI backend (port `8000`) and the Vite React frontend (port `5173`) in two separate terminal windows.

---

## 🐳 Docker Setup (Production Container)

We provide a unified Docker container setup that bundles both the React frontend build assets and the FastAPI server, serving the entire application from a single exposed port.

### 1. Build the Docker Image
Run the builder script in your terminal:
```powershell
.\build_docker.bat
```
This runs a multi-stage Docker build:
- **Stage 1:** Compiles the Vite React assets inside a Node.js container.
- **Stage 2:** Sets up the Python environment, copies the backend code, mounts the compiled frontend build, and exposes port `8000`.

### 2. Run the Container
Start the container and link it with your env file:
```powershell
docker run -d -p 8000:8000 --env-file Backend/.env --name hindsight-container hindsight-agent:latest
```
Access the complete dashboard and API endpoints at: **`http://localhost:8000`**

---

## 🚀 How to Proceed & Test the Agent

Once the application is running:

### A. Run an Audit on the Demo Repo
1. Open the frontend dashboard (`http://localhost:5173` or `http://localhost:8000` under Docker).
2. Set the **Input Type** toggle to **GitHub Crawler**.
3. Input the demo repo path: `11-anos/demo-vulnerable-microservice` and click **Start Audit**.
4. Watch the live SSE (Server-Sent Events) timeline run:
   - **GitHub Crawler** fetches the commit metadata.
   - **Context Agent** classifies modified code files.
   - **Reviewer V1** matches signatures in the Hindsight DB and flags risk.
   - **Specialist Experts** (Git, Cloud Infrastructure, and Code Experts) run parallel analyses on the vulnerabilities.
   - **Big Boss Agent** reviews the inputs and issues a **BLOCKED / REQUIRES_REVIEW** verdict alongside the specific risks.

### B. Trigger Automated Audits via GitHub Webhooks
You can configure GitHub to automatically run audits whenever you push code or open PRs:
1. Navigate to your GitHub repository -> **Settings** -> **Webhooks** -> **Add webhook**.
2. Set **Payload URL** to: `http://<your-public-ip-or-ngrok-domain>/api/webhook/github`.
3. Set **Content type** to `application/json`.
4. Input the **Secret** matching your `.env` file's `GITHUB_WEBHOOK_SECRET`.
5. Select **Just the push event** or **Let me select individual events** (Push, Pull requests).
6. Click **Add webhook**. Any future push will now automatically launch pipeline runs visible in the **Audit Logs** tab.
