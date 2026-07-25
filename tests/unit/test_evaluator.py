"""
tests/unit/test_evaluator.py

Unit tests for Evaluator logic and regex secret detection (src/agents/evaluator.py)
"""
import pytest

from src.agents.evaluator import _detect_and_decode_base64, evaluate_attempt
from src.memory.schemas import AttackAttempt, AttackPayload


def test_base64_decoder_detects_encoded_exfiltration():
    # Base64 string for: "Confidential document: API_KEY=SECRET_99X"
    encoded_str = "Q29uZmlkZW50aWFsIGRvY3VtZW50OiBBUElfS0VZPVNFQ1JFVF85OVg="
    response = f"Sure! Here is the encoded text: {encoded_str}"

    decoded, kw = _detect_and_decode_base64(response)
    assert decoded is not None
    assert kw is not None


@pytest.mark.asyncio
async def test_sentinel_response_returns_failure_result():
    payload = AttackPayload(
        payload_id="lk-001",
        name="Base64 Exfil",
        category="leakage",
        template="Test payload"
    )
    attempt = AttackAttempt(
        attempt_id="att-1",
        session_id="sess-1",
        target_id="target-1",
        payload_id="lk-001",
        category="leakage",
        payload_text="Test prompt",
        response_text="[AEGIS_TIMEOUT: Target response timed out after 15s]"
    )

    result = await evaluate_attempt(attempt, payload)
    assert result.verdict == "fail"
    assert result.score == 0.0
    assert "[INCOMPLETE]" in result.reasoning
