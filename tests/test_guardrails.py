from guardrails import (
    CRISIS_RESOURCE_MESSAGE,
    ELEVATED_RISK,
    ROUTINE_RISK,
    SAFE_FALLBACK_MESSAGE,
    URGENT_RISK,
    apply_output_guardrails,
    local_risk_level,
    validate_bot_response,
    validate_user_message,
)


def test_user_guardrail_blocks_urgent_language():
    result = validate_user_message("I want to end my life")

    assert not result.allowed
    assert result.risk_level == URGENT_RISK
    assert result.reason == "urgent_user_language"
    assert result.replacement == CRISIS_RESOURCE_MESSAGE


def test_user_guardrail_allows_elevated_non_crisis_language():
    result = validate_user_message("I am anxious and exhausted")

    assert result.allowed
    assert result.risk_level == ELEVATED_RISK


def test_output_guardrail_blocks_diagnostic_claims():
    result = validate_bot_response("You have PPD and need treatment.", ROUTINE_RISK)

    assert not result.allowed
    assert result.reason == "diagnosis_claim"
    assert result.replacement == SAFE_FALLBACK_MESSAGE


def test_output_guardrail_blocks_medication_advice():
    result = validate_bot_response("You should start sertraline and increase your dose.", ELEVATED_RISK)

    assert not result.allowed
    assert result.reason == "medical_advice"


def test_output_guardrail_blocks_non_urgent_hotlines():
    result = validate_bot_response("You can call Postpartum Support International for this.", ROUTINE_RISK)

    assert not result.allowed
    assert result.reason == "non_urgent_hotline"


def test_output_guardrail_allows_generic_support_line_language():
    result = validate_bot_response("A doctor, counselor, or support line can help you talk this through.", ELEVATED_RISK)

    assert result.allowed


def test_output_guardrail_allows_crisis_message_for_urgent_risk():
    result = validate_bot_response(CRISIS_RESOURCE_MESSAGE, URGENT_RISK)

    assert result.allowed


def test_apply_output_guardrails_replaces_unsafe_text():
    response = apply_output_guardrails("This confirms postpartum depression.", ROUTINE_RISK)

    assert response == SAFE_FALLBACK_MESSAGE


def test_local_risk_level_keeps_boundary_matching():
    assert local_risk_level("I do not really feel connected") == ROUTINE_RISK
    assert local_risk_level("I feel like things are not real") == URGENT_RISK
