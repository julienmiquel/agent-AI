"""Memory Manager & Context Bloat Compaction for ECG Multi-Agent System.

Implements history compaction (token sliding window & turn summarization), persistent
conversational history storage in Firebase Firestore / DB, and non-blocking asynchronous
memory operations to prevent UI blocking during expensive consolidation tasks.
"""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from src.datastore import datastore
from src.observability import scrub_pii, log_telemetry_event

logger = logging.getLogger(__name__)

# Background executor for non-blocking async memory consolidation
_memory_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ecg_memory_worker")


class MemoryManager:
    """Manages persistent conversation turns, context bloat compaction, and async consolidation."""

    def __init__(self, max_active_turns: int = 8, token_compaction_threshold: int = 2000):
        self.max_active_turns = max_active_turns
        self.token_compaction_threshold = token_compaction_threshold
        self._turn_history: Dict[str, List[Dict[str, Any]]] = {}
        self._compacted_summaries: Dict[str, str] = {}

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieve active conversational turn history for a session."""
        if session_id not in self._turn_history:
            # Try loading from persistent datastore
            session_doc = datastore.get_session(session_id)
            if session_doc and "turn_history" in session_doc:
                self._turn_history[session_id] = session_doc["turn_history"]
            else:
                self._turn_history[session_id] = []
        return self._turn_history[session_id]

    def get_compacted_summary(self, session_id: str) -> Optional[str]:
        """Retrieve executive summary of older compacted conversational turns."""
        if session_id not in self._compacted_summaries:
            session_doc = datastore.get_session(session_id)
            if session_doc and "compacted_summary" in session_doc:
                self._compacted_summaries[session_id] = session_doc["compacted_summary"]
        return self._compacted_summaries.get(session_id)

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (approx. 4 characters per token)."""
        if not text:
            return 0
        return len(str(text)) // 4

    def compact_history_sync(self, session_id: str, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Synchronously compact older turns when sliding window or token threshold is exceeded."""
        total_tokens = sum(
            self.estimate_tokens(t.get("user_prompt", "")) + self.estimate_tokens(str(t.get("agent_response", "")))
            for t in history
        )

        if len(history) <= self.max_active_turns and total_tokens <= self.token_compaction_threshold:
            return {"compacted": False, "history": history}

        logger.info("Context bloat detected for session '%s' (turns=%d, est_tokens=%d). Compacting history...",
                    session_id, len(history), total_tokens)

        # Retain the most recent half of the window
        keep_count = max(2, self.max_active_turns // 2)
        old_turns = history[:-keep_count]
        recent_turns = history[-keep_count:]

        # Create consolidated executive summary of older turns
        summary_points = []
        for i, turn in enumerate(old_turns, 1):
            u_prompt = turn.get("user_prompt", "")[:100]
            a_resp = str(turn.get("agent_response", ""))[:150]
            intent = turn.get("intent", "UNKNOWN")
            summary_points.append(f"[Turn {i} - Intent: {intent}]: User asked: '{u_prompt}'. Agent responded: '{a_resp}'")

        existing_summary = self.get_compacted_summary(session_id) or ""
        new_summary = f"{existing_summary}\n" + "\n".join(summary_points) if existing_summary else "\n".join(summary_points)
        new_summary = new_summary.strip()

        self._turn_history[session_id] = recent_turns
        self._compacted_summaries[session_id] = new_summary

        # Log telemetry event for compaction
        log_telemetry_event(
            event_type="MEMORY_COMPACTION",
            agent_name="MemoryManager",
            message=f"Compacted {len(old_turns)} older turns for session '{session_id}' into executive summary.",
            payload={"session_id": session_id, "compacted_turns_count": len(old_turns), "remaining_turns_count": len(recent_turns)},
        )

        return {"compacted": True, "history": recent_turns, "summary": new_summary}

    def _background_save_and_consolidate(self, session_id: str, turn_record: Dict[str, Any]) -> None:
        """Worker task executed in background thread pool to prevent UI blocking."""
        try:
            start_t = time.time()
            history = self.get_history(session_id)
            history.append(scrub_pii(turn_record))

            # Execute compaction if needed
            compaction_res = self.compact_history_sync(session_id, history)
            active_history = compaction_res["history"]
            compacted_summary = self.get_compacted_summary(session_id)

            # Persist to datastore (Firestore / DB)
            save_payload = {
                "turn_history": active_history,
                "last_turn_at": datetime.now(timezone.utc).isoformat(),
            }
            if compacted_summary:
                save_payload["compacted_summary"] = compacted_summary

            datastore.save_session(session_id, save_payload)
            dur_ms = round((time.time() - start_t) * 1000, 2)
            logger.info("Async memory consolidation & Firestore persistence completed in %s ms for session '%s'", dur_ms, session_id)
        except Exception as e:
            logger.error("Async background memory consolidation error for session '%s': %s", session_id, str(e))

    def add_turn_async(
        self,
        session_id: str,
        user_prompt: str,
        agent_response: Any,
        intent: str = "UNKNOWN",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Dispatch memory record saving and consolidation as a non-blocking asynchronous task."""
        turn_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_prompt": user_prompt,
            "agent_response": agent_response,
            "intent": intent,
            "metadata": metadata or {},
        }

        # Submit to background executor so LLM response returns immediately without UI latency
        _memory_executor.submit(self._background_save_and_consolidate, session_id, turn_record)
        logger.debug("Dispatched async memory consolidation for session '%s'", session_id)


# Global Memory Manager Instance
memory_manager = MemoryManager()
