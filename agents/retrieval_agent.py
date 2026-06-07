from typing import Dict, Any, List
from state import SharedGraphState
from agents.utils import get_db

def retrieval_agent(state: SharedGraphState) -> Dict[str, Any]:
    """
    Retrieval Agent executes queries by searching the Hindsight DB or generating
    matching simulated log / issue telemetry to support the domain specialists.
    """
    queries = state.get("retrieval_queries", [])
    print(f">>> Retrieval Agent: Simulating API & Log telemetry queries for: {queries}")
    
    db = get_db()
    retrieved_logs: List[Dict[str, Any]] = []
    
    # 1. Fetch matching documents from database using query keywords
    for q in queries:
        incidents = db.query_incidents(q, limit=1)
        for inc in incidents:
            log_item = {
                "source": "Hindsight Incident DB",
                "type": "Historical Incident Record",
                "id": inc["id"],
                "title": inc["title"],
                "description": inc["description"],
                "mitigation_summary": inc["mitigation"]
            }
            if log_item not in retrieved_logs:
                retrieved_logs.append(log_item)
                
    # 2. Append simulated live logs / telemetry matching the query context
    # This simulates querying CloudWatch, Datadog, or GitHub API
    for q in queries:
        q_lower = q.lower()
        if "socket" in q_lower or "websocket" in q_lower or "leak" in q_lower or "file" in q_lower:
            retrieved_logs.append({
                "source": "CloudWatch Logs",
                "type": "Runtime Exception Trace",
                "log_level": "ERROR",
                "message": "[2026-06-07 10:14:22 UTC] ConnectionPool - java.io.IOException: Too many open files at socket.accept()",
                "context": "Connection stuck in CLOSE_WAIT state. Active connections: 4096 (Max: 4096)."
            })
        elif "ssh" in q_lower or "port" in q_lower or "security group" in q_lower or "0.0.0.0" in q_lower:
            retrieved_logs.append({
                "source": "AWS CloudTrail Audits",
                "type": "Compliance Guardrail Alert",
                "log_level": "WARNING",
                "message": "AWS security group rule modified by developer. Port 22 SSH ingress open to world.",
                "context": "Resource: sg-01c8a14ff2ba. Rule allows CIDR 0.0.0.0/0. Policy violation."
            })
        elif "secret" in q_lower or "key" in q_lower or "token" in q_lower or "env" in q_lower:
            retrieved_logs.append({
                "source": "GitSecretGuard Scanner",
                "type": "Pre-commit Scan Outage",
                "log_level": "CRITICAL",
                "message": "Potential secret or private key pattern detected in committed file.",
                "context": "File: .env, Line containing: DATABASE_URL=postgresql://db_user:password@prod-host..."
            })
        elif "sql" in q_lower or "inject" in q_lower or "string" in q_lower:
            retrieved_logs.append({
                "source": "Snyk Security Scanner",
                "type": "Static Analysis Alert",
                "log_level": "HIGH",
                "message": "SQL Injection vulnerability. Raw f-string input query format detected.",
                "context": "In file app/users.py: cursor.execute(f'SELECT * FROM users WHERE ID = {user_id}')"
            })
        elif "docker" in q_lower or "root" in q_lower or "base image" in q_lower:
            retrieved_logs.append({
                "source": "Trivy Container Scanner",
                "type": "Vulnerability Scan",
                "log_level": "HIGH",
                "message": "Base image ubuntu:latest or node:latest has 47 vulnerabilities.",
                "context": "Container is configured to run as root. Recommended fix: 'USER node' or alpine base."
            })

    # If no logs could be retrieved/generated, provide a generic log to assist sub-agents
    if not retrieved_logs:
        retrieved_logs.append({
            "source": "Default DevOps Logger",
            "type": "General Telemetry",
            "log_level": "INFO",
            "message": f"Successfully initialized retrieval for queries: {queries}",
            "context": "No active outages or high-priority warnings retrieved."
        })

    print(f"Retrieval Agent: Fetched {len(retrieved_logs)} log telemetry context entries.")
    return {
        "retrieved_logs": retrieved_logs
    }
