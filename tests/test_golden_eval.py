"""Automated Golden Dataset Evaluation Suite for Company Multi-Agent System.

Executes static regression benchmarking against ground-truth trajectories in `golden_dataset.json`,
verifying intent classification accuracy, SQL keyword generation, HITL interception rules,
prompt injection guardrail blocks, and active PII sanitization.
"""

import json
import os
import pytest
from typing import Dict, Any, List
from src.agents.supervisor import Company_Supervisor_Agent, StateSession
from src.observability import scrub_pii, scrub_string


def load_golden_dataset() -> List[Dict[str, Any]]:
    """Loads the golden dataset benchmark cases from disk."""
    dataset_path = os.path.join(os.path.dirname(__file__), "golden_dataset.json")
    with open(dataset_path, "r", encoding="utf-8") as f:
        return json.load(f)


GOLDEN_CASES = load_golden_dataset()


@pytest.fixture
def supervisor():
    """Returns a fresh instance of the Company Supervisor Agent."""
    return Company_Supervisor_Agent()


@pytest.mark.parametrize("case", GOLDEN_CASES, ids=lambda c: c["test_id"])
def test_golden_trajectory_eval(supervisor, case):
    """Executes automated regression evaluation against each golden benchmark case."""
    test_id = case["test_id"]
    category = case["category"]
    prompt = case["prompt"]

    # Initialize isolated session for test case
    session = StateSession(session_id=f"eval_session_{test_id}", user_id="eval_runner")

    if category == "PII_REDACTION":
        # Direct verification of PII scrubbing mechanism
        scrubbed_prompt = scrub_string(prompt)
        for expected_redaction in case["expected_pii_redacted_strings"]:
            assert expected_redaction in scrubbed_prompt, (
                f"[{test_id}] Failed PII redaction: Expected '{expected_redaction}' in scrubbed output: '{scrubbed_prompt}'"
            )
        return

    # Execute supervisor turn
    result = supervisor.process_turn(prompt, session=session, confirmed=False)

    # 1. Verify Execution Status
    expected_status = case["expected_status"]
    assert result["status"] == expected_status, (
        f"[{test_id}] Status mismatch: Expected '{expected_status}', got '{result['status']}'. Message: {result.get('message')}"
    )

    # 2. Verify Intent Classification (when applicable)
    if "expected_intent" in case and case["expected_intent"] != "UNKNOWN":
        assert result.get("intent") == case["expected_intent"], (
            f"[{test_id}] Intent mismatch: Expected '{case['expected_intent']}', got '{result.get('intent')}'"
        )

    # 3. Verify SQL Generation Keywords (for Yield Analytics)
    if "expected_sql_keywords" in case:
        sql_queries = result.get("sql_queries") or (result.get("agent_output") or {}).get("sql_queries", [])
        assert sql_queries, f"[{test_id}] No SQL queries generated for yield analytics case."
        combined_sql = " ".join(sql_queries)
        for kw in case["expected_sql_keywords"]:
            assert kw in combined_sql, (
                f"[{test_id}] Missing expected SQL keyword '{kw}' in generated query: {combined_sql}"
            )

    # 4. Verify Widget / HITL Manifest structure
    if "expected_widget_type" in case:
        widget = result.get("widget") or (result.get("agent_output") or {}).get("widget", {})
        assert widget.get("widget_type") == case["expected_widget_type"], (
            f"[{test_id}] Widget type mismatch: Expected '{case['expected_widget_type']}', got '{widget.get('widget_type')}'"
        )
        if "expected_manifest_keys" in case:
            manifest = widget.get("manifest", {})
            for mkey in case["expected_manifest_keys"]:
                assert mkey in manifest, (
                    f"[{test_id}] Missing expected manifest key '{mkey}' in HITL card: {manifest}"
                )

    # 5. Verify Guardrail Violation Error Messages
    if "expected_error_substring" in case:
        msg = str(result.get("message") or result.get("error") or "")
        assert case["expected_error_substring"].lower() in msg.lower(), (
            f"[{test_id}] Expected error substring '{case['expected_error_substring']}' not found in message: '{msg}'"
        )
