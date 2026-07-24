"""Structured JSON Logging & Intent vs. Outcome Capture.

Implements structured JSON log formatting with rich metadata and explicit tracking
of agent intended actions prior to execution versus actual outcomes after execution,
integrated with automated PII redaction.
"""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from src.observability.pii_scrubber import scrub_pii
from src.observability.tracer import tracer


class JSONFormatter(logging.Formatter):
    """Formatter that outputs JSON strings with rich telemetry metadata and PII scrubbing."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "severity": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": tracer.get_current_trace_id(),
        }

        # Attach active span ID if in a trace context
        if tracer._current_span_stack:
            log_obj["span_id"] = tracer._current_span_stack[-1].span_id
            log_obj["parent_span_id"] = tracer._current_span_stack[-1].parent_span_id

        # Merge extra telemetry attributes if present on record
        if hasattr(record, "telemetry_payload") and isinstance(record.telemetry_payload, dict):
            log_obj["telemetry"] = scrub_pii(record.telemetry_payload)

        # Handle exceptions
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(scrub_pii(log_obj), ensure_ascii=False)


def setup_structured_logging(level: int = logging.INFO) -> None:
    """Configures root logger to use structured JSON output."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(console_handler)


def log_telemetry_event(
    event_type: str,
    agent_name: str,
    message: str,
    payload: Optional[Dict[str, Any]] = None,
    level: int = logging.INFO,
) -> Dict[str, Any]:
    """Emit a structured telemetry event with automated PII redaction."""
    telemetry_data = {
        "event_type": event_type,
        "agent_name": agent_name,
        "trace_id": tracer.get_current_trace_id(),
        "payload": scrub_pii(payload or {}),
    }
    if tracer._current_span_stack:
        telemetry_data["span_id"] = tracer._current_span_stack[-1].span_id
        tracer._current_span_stack[-1].add_event(event_type, telemetry_data["payload"])

    logger = logging.getLogger(agent_name)
    logger.log(level, message, extra={"telemetry_payload": telemetry_data})
    return telemetry_data


def log_intent_capture(
    agent_name: str,
    intended_action: str,
    parameters: Dict[str, Any],
    user_goal: Optional[str] = None,
    tool_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Log an INTENT_CAPTURE event prior to agent or tool execution."""
    payload = {
        "intended_action": intended_action,
        "tool_name": tool_name or "DIRECT_AGENT_ACTION",
        "user_goal": user_goal or intended_action,
        "parameters": parameters,
        "execution_stage": "PRE_EXECUTION",
    }
    return log_telemetry_event(
        event_type="INTENT_CAPTURE",
        agent_name=agent_name,
        message=f"Intent Captured: [{agent_name}] intends to execute '{intended_action}'",
        payload=payload,
        level=logging.INFO,
    )


def log_outcome_capture(
    agent_name: str,
    outcome_status: str,
    result_summary: Any,
    duration_ms: float,
    intended_action: Optional[str] = None,
    tool_name: Optional[str] = None,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    """Log an OUTCOME_CAPTURE event following agent or tool execution."""
    level = logging.ERROR if outcome_status in {"ERROR", "VALIDATION_ERROR", "REJECTED"} else logging.INFO
    payload = {
        "outcome_status": outcome_status,
        "intended_action": intended_action,
        "tool_name": tool_name or "DIRECT_AGENT_ACTION",
        "duration_ms": duration_ms,
        "result_summary": result_summary,
        "error": error,
        "execution_stage": "POST_EXECUTION",
    }
    return log_telemetry_event(
        event_type="OUTCOME_CAPTURE",
        agent_name=agent_name,
        message=f"Outcome Captured: [{agent_name}] finished '{intended_action or tool_name}' with status '{outcome_status}' in {duration_ms}ms",
        payload=payload,
        level=level,
    )
