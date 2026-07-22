"""Security Guardrails & Self-Evaluation Policy Plugins.

Implements input screening for prompt injection and malicious payloads, business parameter
boundary enforcement, and a self-evaluation verification plugin that inspects agent outputs
prior to user delivery.
"""

import logging
import re
from typing import Any, Dict, List, Optional
from src.observability import log_telemetry_event, scrub_pii

logger = logging.getLogger(__name__)

# Malicious prompt injection and destructive SQL/system command keywords
PROMPT_INJECTION_PATTERNS = [
    r'(?i)\b(ignore|disregard|forget)\b.*\b(previous|all|above|system)\s+(instructions|prompt|rules)\b',
    r'(?i)\b(you are now|act as|simulate)\b.*\b(unrestricted|unfiltered|jailbroken|developer mode|root)\b',
    r'(?i)\b(drop\s+table|truncate\s+table|delete\s+from|alter\s+table|exec\s*\()\b',
    r'(?i)<script>|javascript:|onerror=|onload=',
    r'(?i)\b(override|bypass|disable)\b.*\b(guardrails|hitl|security|confirmation|approval)\b',
]

COMPILED_INJECTION_REGEX = [re.compile(p) for p in PROMPT_INJECTION_PATTERNS]


class SecurityGuardrailError(Exception):
    """Raised when a security or policy guardrail violation occurs."""
    pass


def screen_input_guardrail(prompt: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """Screens user input for prompt injection, SQL injection, and policy evasion attempts."""
    if not prompt or not isinstance(prompt, str):
        return {"passed": True, "violation": None}

    for regex in COMPILED_INJECTION_REGEX:
        match = regex.search(prompt)
        if match:
            violation_msg = f"Potential prompt injection or destructive command detected matching pattern '{match.group(0)}'."
            logger.warning("Security Guardrail Blocked Prompt [%s]: %s", session_id, violation_msg)
            
            log_telemetry_event(
                event_type="SECURITY_GUARDRAIL_VIOLATION",
                agent_name="SecurityGuardrail",
                message=f"Blocked malicious user prompt for session '{session_id}'",
                payload={"prompt_snippet": prompt[:100], "violation": violation_msg},
                level=logging.ERROR,
            )
            return {
                "passed": False,
                "violation": violation_msg,
                "status": "VALIDATION_ERROR",
                "recovery_instruction": "Your prompt was flagged by our automated security guardrails for containing restricted keywords or instructions. Please reformulate your request to focus on ECG Yield, PMS, or Marketing operations.",
            }

    return {"passed": True, "violation": None}


def check_business_guardrail(intent: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Enforces strict business rules and boundary constraints on tool parameters."""
    # Guardrail 1: Marketing discount percentage cap <= 50%
    if intent == "MARKETING_CAMPAIGN" or "discount_percentage" in parameters:
        disc = parameters.get("discount_percentage")
        if disc is not None:
            try:
                disc_val = int(disc)
                if disc_val > 50:
                    violation = f"Discount percentage ({disc_val}%) exceeds maximum allowable business guardrail limit of 50%."
                    logger.warning("Business Guardrail Blocked: %s", violation)
                    return {
                        "passed": False,
                        "violation": violation,
                        "status": "VALIDATION_ERROR",
                        "recovery_instruction": "The requested discount exceeds the maximum authorized threshold of 50%. Please specify a discount between 5% and 50% or request manager override approval.",
                    }
                if disc_val < 0:
                    return {
                        "passed": False,
                        "violation": "Discount percentage cannot be negative.",
                        "status": "VALIDATION_ERROR",
                        "recovery_instruction": "Please specify a positive discount percentage between 0% and 50%.",
                    }
            except (ValueError, TypeError):
                pass

    # Guardrail 2: Campsite ID validation
    if "campsite_id" in parameters and parameters["campsite_id"]:
        cid = str(parameters["campsite_id"]).strip().upper()
        valid_prefixes = ("LA_SIRENE", "DOLMEN_COVE", "HIPOCAMP", "MARIS_SOL", "PARC_VERDON")
        if not any(cid.startswith(p) for p in valid_prefixes):
            violation = f"Campsite ID '{cid}' does not match any recognized ECG property prefix."
            return {
                "passed": False,
                "violation": violation,
                "status": "VALIDATION_ERROR",
                "recovery_instruction": f"Please verify the campsite identifier. Recognized properties include prefixes: {valid_prefixes}.",
            }

    return {"passed": True, "violation": None}


def self_eval_output_verify(
    agent_name: str,
    prompt: str,
    agent_output: Dict[str, Any],
    confirmed: bool = False,
) -> Dict[str, Any]:
    """Self-evaluation verification plugin inspecting agent output prior to user delivery."""
    status = agent_output.get("status", "SUCCESS")
    if status in {"ERROR", "VALIDATION_ERROR", "CANCELLED", "PENDING_CONFIRMATION"}:
        # Pass through non-success or HITL pending states directly
        return agent_output

    # Verification 1: Prevent unapproved state mutations without HITL confirmation
    intent = agent_output.get("intent", "")
    if intent in {"PMS_OPERATIONS", "MARKETING_CAMPAIGN"} and not confirmed:
        # Check if the output actually mutated state
        widget = agent_output.get("widget") or {}
        if widget.get("widget_type") in {"PMS_INVENTORY_UPDATE", "CRM_FLASH_CAMPAIGN"} and widget.get("status") != "PENDING_CONFIRMATION":
            violation = f"Self-Eval Policy Violation: [{agent_name}] attempted to execute a mutating action ({intent}) without explicit Human-in-the-Loop confirmation."
            logger.error(violation)
            log_telemetry_event(
                event_type="SELF_EVAL_POLICY_VIOLATION",
                agent_name=agent_name,
                message=violation,
                payload={"intent": intent, "agent_output_summary": scrub_pii(agent_output)},
                level=logging.ERROR,
            )
            return {
                "status": "ERROR",
                "error": violation,
                "message": "Security policy intervention: State mutating actions must undergo explicit human confirmation before execution.",
                "recovery_instruction": "Please ask the user for explicit confirmation (YES/NO) before executing this mutating operation.",
            }

    # Verification 2: Ensure copywriting text is localized and non-empty for marketing
    if intent == "MARKETING_CAMPAIGN":
        copy_text = agent_output.get("copywriting_text") or (agent_output.get("widget") or {}).get("copywriting_text")
        if copy_text and isinstance(copy_text, str):
            if len(copy_text.strip()) < 10:
                logger.warning("Self-Eval Warning: Generated promotional copy is too short (< 10 chars).")
                agent_output["self_eval_note"] = "Copywriting verified: Text is brief; consider expanding for higher customer engagement."

    # Verification 3: Sanitize final output payload of any accidental PII or token leakage
    verified_output = scrub_pii(agent_output)
    verified_output["self_eval_verified"] = True
    return verified_output
