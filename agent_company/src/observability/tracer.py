"""OpenTelemetry Distributed Tracing & Span Tracking.

Provides distributed tracing capabilities to link spans and trace a request from root
query through intent routing, child agent execution, and tool invocations. Supports
OpenTelemetry SDK if installed, with robust fallback to structured in-memory span tracking.
"""

import time
import uuid
import logging
from typing import Any, Dict, List, Optional
from contextlib import contextmanager
from src.observability.pii_scrubber import scrub_pii

logger = logging.getLogger(__name__)

# Attempt importing opentelemetry
try:
    from opentelemetry import trace as otel_trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False


class Span:
    """Represents a distributed tracing span with parent-child linkage and attribute tracking."""

    def __init__(self, name: str, trace_id: str, span_id: str, parent_span_id: Optional[str] = None):
        self.name = name
        self.trace_id = trace_id
        self.span_id = span_id
        self.parent_span_id = parent_span_id
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.status: str = "IN_PROGRESS"
        self.attributes: Dict[str, Any] = {}
        self.events: List[Dict[str, Any]] = []

    def set_attribute(self, key: str, value: Any) -> None:
        """Set a metadata attribute on the span, automatically scrubbing PII."""
        self.attributes[key] = scrub_pii(value)

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add a timestamped event to the span."""
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": scrub_pii(attributes or {}),
        })

    def set_status(self, status: str) -> None:
        """Set the completion status of the span (e.g. OK, ERROR)."""
        self.status = status

    def end(self) -> Dict[str, Any]:
        """End the span and return its serialized representation."""
        self.end_time = time.time()
        duration_ms = round((self.end_time - self.start_time) * 1000, 2)
        span_dict = {
            "name": self.name,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": duration_ms,
            "status": self.status,
            "attributes": self.attributes,
            "events": self.events,
        }
        return span_dict


class CompanyTracer:
    """Distributed Tracer managing request trace contexts and span execution."""

    def __init__(self, service_name: str = "agent-company-service"):
        self.service_name = service_name
        self.active_spans: Dict[str, Span] = {}
        self.completed_spans: List[Dict[str, Any]] = []
        self._current_trace_id: Optional[str] = None
        self._current_span_stack: List[Span] = []

        if OTEL_AVAILABLE:
            try:
                provider = TracerProvider()
                otel_trace.set_tracer_provider(provider)
                self.otel_tracer = otel_trace.get_tracer(self.service_name)
                logger.info("OpenTelemetry SDK initialized for service '%s'", self.service_name)
            except Exception as e:
                logger.warning("Failed to initialize OpenTelemetry SDK: %s. Using standalone distributed tracer.", str(e))
                self.otel_tracer = None
        else:
            self.otel_tracer = None
            logger.info("OpenTelemetry SDK not installed. Using standalone distributed tracer.")

    def start_trace(self, trace_id: Optional[str] = None) -> str:
        """Start a new distributed trace context."""
        self._current_trace_id = trace_id or f"trace-{uuid.uuid4().hex[:16]}"
        self._current_span_stack = []
        return self._current_trace_id

    def get_current_trace_id(self) -> str:
        """Get or initialize the current trace ID."""
        if not self._current_trace_id:
            return self.start_trace()
        return self._current_trace_id

    @contextmanager
    def span(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Context manager to start and automatically end a distributed tracing span."""
        trace_id = self.get_current_trace_id()
        span_id = f"span-{uuid.uuid4().hex[:12]}"
        parent_span_id = self._current_span_stack[-1].span_id if self._current_span_stack else None

        new_span = Span(name=name, trace_id=trace_id, span_id=span_id, parent_span_id=parent_span_id)
        if attributes:
            for k, v in attributes.items():
                new_span.set_attribute(k, v)

        self._current_span_stack.append(new_span)
        self.active_spans[span_id] = new_span

        try:
            yield new_span
            if new_span.status == "IN_PROGRESS":
                new_span.set_status("OK")
        except Exception as e:
            new_span.set_status("ERROR")
            new_span.set_attribute("error.message", str(e))
            new_span.set_attribute("error.type", type(e).__name__)
            raise
        finally:
            if self._current_span_stack and self._current_span_stack[-1].span_id == span_id:
                self._current_span_stack.pop()
            span_dict = new_span.end()
            self.completed_spans.append(span_dict)
            self.active_spans.pop(span_id, None)
            logger.debug("Ended span '%s' (duration: %s ms, status: %s)", name, span_dict["duration_ms"], span_dict["status"])

    def get_trace_summary(self, trace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve all completed spans for a given trace_id."""
        t_id = trace_id or self._current_trace_id
        return [s for s in self.completed_spans if s["trace_id"] == t_id]


# Global Tracer Instance
tracer = CompanyTracer()
