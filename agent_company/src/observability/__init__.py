"""Observability & Telemetry Suite for Company Multi-Agent System.

Exports structured JSON logging, distributed OpenTelemetry tracing, intent vs. outcome
capture, and automated PII scrubbing mechanisms.
"""

from src.observability.pii_scrubber import scrub_pii, scrub_string
from src.observability.tracer import tracer, CompanyTracer, Span
from src.observability.logger import (
    JSONFormatter,
    setup_structured_logging,
    log_telemetry_event,
    log_intent_capture,
    log_outcome_capture,
)

__all__ = [
    "scrub_pii",
    "scrub_string",
    "tracer",
    "CompanyTracer",
    "Span",
    "JSONFormatter",
    "setup_structured_logging",
    "log_telemetry_event",
    "log_intent_capture",
    "log_outcome_capture",
]
