import uuid
import re
from typing import Dict, Any
from state import SharedGraphState
from agents.utils import get_db

def context_agent(state: SharedGraphState) -> Dict[str, Any]:
    """
    Ingests git_diff, extracts file paths and formats, generates a unique session
    id, and logs/indexes the session metadata in the Hindsight database.
    """
    print(">>> Context Agent: Ingesting Git Diff and Extracting Metadata...")
    git_diff = state.get("git_diff", "")
    
    # Simple parser to find files changed in the git diff
    changed_files = []
    file_matches = re.findall(r"(\+\+\+ b/|--- a/)(.*)", git_diff)
    for match in file_matches:
        file_path = match[1].strip()
        if file_path and file_path not in changed_files and file_path != "/dev/null":
            changed_files.append(file_path)

    # Classify files based on path patterns
    file_types = {
        "cloud_infra": [],
        "git_meta": [],
        "app_code": []
    }
    
    for f in changed_files:
        if any(f.endswith(ext) for ext in [".tf", ".yaml", ".yml", "Dockerfile", "docker-compose.yml"]):
            file_types["cloud_infra"].append(f)
        elif any(f.endswith(ext) for ext in [".gitignore", ".github/workflows", ".gitlab-ci.yml"]):
            file_types["git_meta"].append(f)
        else:
            file_types["app_code"].append(f)

    # Prepare session metadata
    metadata = {
        "changed_files": changed_files,
        "classification": file_types,
        "author": state.get("metadata", {}).get("author", "unknown_developer"),
        "timestamp": state.get("metadata", {}).get("timestamp", "2026-06-07T13:55:00Z")
    }

    # Retrieve or generate session ID
    session_id = state.get("hindsight_session_id")
    if not session_id:
        session_id = f"session_{uuid.uuid4().hex[:10]}"

    # Index session in Hindsight
    db = get_db()
    db.save_session(session_id, git_diff, metadata)

    loop_count = state.get("loop_count", 0)

    print(f"Context Agent: Created Session ID: {session_id}")
    print(f"Context Agent: Metadata Extracted: {metadata}")

    return {
        "hindsight_session_id": session_id,
        "metadata": metadata,
        "loop_count": loop_count
    }
