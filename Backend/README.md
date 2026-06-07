# Hindsight-Powered DevOps Pipeline Agent

An event-driven, multi-agent pipeline acting as an "Operational Brain" for CI/CD workflows. It intercepts risky code and cloud modifications before deployment by matching changes against a semantic database of historical failures (Hindsight memory layer).

This repository contains a local, barebones MVP built using **LangGraph (Python)** and **Groq (LangChain)**.

## Project Structure

```
devops_pipeline_agent/
├── .env.example              # Environment variables template
├── requirements.txt          # Python dependencies
├── README.md                 # Main setup guide
├── agent_docs.md             # Detailed specifications for each agent
├── database.json             # Hindsight Database (historical incidents)
├── hindsight_db.py           # Database wrapper and keyword-matcher
├── state.py                  # Shared graph state (TypedDict with reducer)
├── graph.py                  # LangGraph workflow wiring and conditional routing
├── agents/                   # Agent Node definitions
│   ├── __init__.py
│   ├── utils.py              # LLM and DB shared handlers
│   ├── context_agent.py      # Git diff parser and session indexing
│   ├── reviewer_v1.py        # Semantic triage (Reviewer V1)
│   ├── reviewer_v2.py        # Query strategy planner (Reviewer V2)
│   ├── retrieval_agent.py    # Log/telemetry gatherer
│   ├── git_expert.py         # Git structure & secrets auditor
│   ├── cloud_expert.py       # Cloud IaC & container configuration auditor
│   ├── code_expert.py        # Application source code leak auditor
│   └── big_boss.py           # Director orchestrator and loopback manager
└── test_pipeline.py          # Interactive CLI test harness
```

## System Architecture

```
                  ┌───────────────┐
                  │  START EDGE   │
                  └───────┬───────┘
                          │
                          ▼
             ┌─────────────────────────┐
             │  Node: context_agent    │ ◄─────────────────────────┐
             └────────────┬────────────┘                           │
                          │                                        │
                          ▼                                        │
             ┌─────────────────────────┐                           │
             │  Node: reviewer_v1      │                           │
             └────────────┬────────────┘                           │
                          │                                        │
                          ▼                                        │
             ┌─────────────────────────┐                           │
             │  Conditional Router     ├─────── [ No Risk ] ────┐  │
             └────────────┬────────────┘                        │  │
                          │                                     │  │
                     [ Risk Found ]                             │  │
                          │                                     │  │
                          ▼                                     │  │
             ┌─────────────────────────┐                        │  │
             │  Node: reviewer_v2      │                        │  │
             └────────────┬────────────┘                        │  │
                          │                                     │  │
                          ▼                                     │  │
             ┌─────────────────────────┐                        │  │
             │  Node: retrieval_agent  │                        │  │
             └────────────┬────────────┘                        │  │
                          │                                     │  │
            ┌─────────────┴─────────────┐                       │  │
            │  PARALLEL FAN-OUT EDGES   │                       │  │
            └──────┬──────┬──────┬──────┘                       │  │
                   │      │      │                              │  │
         ┌─────────┘      │      └─────────┐                    │  │
         ▼                ▼                ▼                    │  │
  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │  │
  │  Node:       │ │  Node:       │ │  Node:       │            │  │
  │  git_expert  │ │  cloud_expert│ │  code_expert │            │  │
  └────────┬─────┘ └──────┬───────┘ └──────┬───────┘            │  │
           │              │                │                    │  │
           └──────────────┼────────────────┘                    │  │
                          │                                     │  │
                          ▼ (Fan-In Join)                       │  │
             ┌─────────────────────────┐                        │  │
             │   Node: big_boss        │                        │  │
             └────────────┬────────────┘                        │  │
                          │                                     │  │
                          ▼                                     │  │
             ┌─────────────────────────┐                        │  │
             │  Conditional Router     ├─ [ Needs Re-Review ] ──┘  │
             └────────────┬────────────┘                           │
                          │                                        │
                    [ Approved ]                                   │
                          │                                        │
                          ▼                                        │
                  ┌───────────────┐                                │
                  │   END EDGE    │ ◄──────────────────────────────┘
                  └───────────────┘
```

## Setup Instructions

### 1. Prerequisites
Ensure you have **Python 3.9+** installed on your machine.

### 2. Install Dependencies
Create a virtual environment, activate it, and install the required packages:

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables Setup
Copy the `.env.example` file to `.env`:

```bash
copy .env.example .env
```

Open `.env` and fill in your **Groq API Key**:
```ini
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
GROQ_MODEL=llama3-70b-8192
```

## Running the Test Suite

Execute the interactive test harness:

```bash
python test_pipeline.py
```

You will see a prompt:
```
Available Scenarios:
1. Run Scenario 1: Clean Code Change (Expect fast bypass)
2. Run Scenario 2: Unsafe Infra Code Change (Expect Security Block)
3. Run Scenario 3: Unsafe WebSocket Code Change (Expect Logic Block + Reflection)
4. Run All Scenarios sequentially

Enter scenario number [1-4]:
```

Choose a scenario to run. The script will invoke the LangGraph pipeline, log node transitions in the console, and render the final synthesized markdown DevOps audit report.

### One-shot setup and test

To install requirements and immediately run the backend test harness, use:

```bash
cd Backend
bash setup_and_test.sh
```

By default, the script creates `Backend/venv`, loads `Backend/.env` if it exists, installs `requirements.txt`, and runs scenario `4` (all scenarios). You can override the defaults with environment variables:

```bash
CREATE_VENV=0 SCENARIO=1 bash setup_and_test.sh
```
