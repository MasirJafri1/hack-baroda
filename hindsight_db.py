import json
import os
from typing import List, Dict, Any

class HindsightDB:
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), "database.json")
        self.db_path = db_path
        self.incidents = self._load_db()

    def _load_db(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.db_path):
            return []
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading Hindsight DB: {e}")
            return []

    def save_session(self, session_id: str, git_diff: str, metadata: Dict[str, Any]):
        """
        Simulates indexing the current execution session into the hindsight memory layer.
        """
        # In a production system, this would index the diff into a vector store.
        # For the MVP, we print it to confirm indexing and could optionally write to a log.
        session_log_path = os.path.join(os.path.dirname(__file__), "sessions_index.jsonl")
        log_entry = {
            "session_id": session_id,
            "metadata": metadata,
            "git_diff_preview": git_diff[:200] + "..." if len(git_diff) > 200 else git_diff
        }
        try:
            with open(session_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            print(f"Error logging session: {e}")

    def query_incidents(self, query_text: str, limit: int = 2) -> List[Dict[str, Any]]:
        """
        Retrieves matching historical incidents by comparing keywords and symptoms
        against the query text (case-insensitive keyword matching).
        Ranks them based on how many keywords/symptoms match.
        """
        query_lower = query_text.lower()
        scored_incidents = []

        for incident in self.incidents:
            score = 0
            # Check title and description
            if incident["title"].lower() in query_lower:
                score += 5
            if any(word in query_lower for word in incident["title"].lower().split()):
                score += 1

            # Check keywords
            for kw in incident.get("keywords", []):
                if kw.lower() in query_lower:
                    score += 3

            # Check symptoms
            for symptom in incident.get("symptoms", []):
                if symptom.lower() in query_lower:
                    score += 4

            if score > 0:
                scored_incidents.append((score, incident))

        # Sort by score descending
        scored_incidents.sort(key=lambda x: x[0], reverse=True)
        results = [inc for _, inc in scored_incidents[:limit]]
        
        # If no keywords matched, return a default incident just to demonstrate deep dive if query seems generic, 
        # or empty if truly clean. For our tests, we want deterministic behavior.
        return results

    def get_all_incidents(self) -> List[Dict[str, Any]]:
        return self.incidents
