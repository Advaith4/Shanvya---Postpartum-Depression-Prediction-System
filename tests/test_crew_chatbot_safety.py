from crew_chatbot import (
    CRISIS_RESOURCE_MESSAGE,
    ELEVATED_RISK,
    ROUTINE_RISK,
    URGENT_RISK,
    build_user_context_summary,
    generate_crewai_chat_response,
    get_supportive_fallback,
    has_crisis_language,
    local_risk_level,
)


def test_crisis_keywords_are_hard_gated_without_groq_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    response = generate_crewai_chat_response("I want to harm myself")

    assert response == CRISIS_RESOURCE_MESSAGE
    assert "immediate human support" in response


def test_harm_to_baby_language_is_urgent():
    assert has_crisis_language("I am scared I might hurt my baby")
    assert local_risk_level("I am scared I might hurt my baby") == URGENT_RISK


def test_psychosis_adjacent_language_is_urgent():
    assert has_crisis_language("I am hearing voices and losing my mind")
    assert local_risk_level("I am hearing voices and losing my mind") == URGENT_RISK


def test_elevated_distress_is_not_routine():
    assert local_risk_level("I feel hopeless and cannot cope") == ELEVATED_RISK


def test_greeting_stays_routine():
    assert local_risk_level("hello") == ROUTINE_RISK


def test_greeting_detection_does_not_match_inside_words():
    response = get_supportive_fallback("this is hard")

    assert not response.startswith("Hello")
    assert "keep track as we go" in response
    assert "What happened today" in response


def test_not_really_does_not_trigger_not_real_crisis_phrase():
    message = "I do not really feel connected to my baby"

    assert not has_crisis_language(message)
    assert local_risk_level(message) == ROUTINE_RISK


def test_fallback_uses_crisis_message_for_urgent_language():
    response = get_supportive_fallback("I want to end my life")

    assert response == CRISIS_RESOURCE_MESSAGE


def test_fallback_answers_memory_question_clearly():
    response = get_supportive_fallback("do you remember my choices?")

    assert "remember what you share in this chat session" in response
    assert "screening choices" in response


def test_fallback_uses_saved_screening_context_for_memory_question():
    user_context = {
        "risk_level": "Moderate postpartum distress risk",
        "epds_score": 12,
        "concern_areas": ["sleep difficulty", "anxiety"],
        "notable_responses": [
            {"label": "sleep difficulty", "response": "Two or more days a week"},
            {"label": "anxiety", "response": "Yes"},
        ],
    }

    response = get_supportive_fallback("what was my result?", user_context=user_context)

    assert "Moderate postpartum distress risk" in response
    assert "12/30" in response
    assert "sleep difficulty" in response
    assert "anxiety" in response


def test_user_context_summary_combines_screening_and_chat_history():
    history = [{"role": "user", "content": "I am exhausted and anxious"}]
    user_context = {
        "risk_level": "High postpartum distress risk",
        "epds_score": 15,
        "concern_areas": ["guilt"],
        "notable_responses": [],
    }

    summary = build_user_context_summary(history, user_context, "sleep is hard")

    assert "High postpartum distress risk" in summary
    assert "15/30" in summary
    assert "guilt" in summary
    assert "sleep difficulty" in summary
    assert "anxiety" in summary


def test_fallback_depression_response_is_specific():
    response = get_supportive_fallback("im depressed")

    assert "depressed" in response
    assert "sadness" in response
    assert "numbness" in response


def test_fallback_continues_thread_after_short_affirming_answer():
    history = [
        {"role": "user", "content": "I am anxious and not sleeping"},
        {
            "role": "assistant",
            "content": "Is the anxiety mostly about the baby, your body, or the day ahead?",
        },
    ]

    response = get_supportive_fallback("yes", history)

    assert "Let us stay with" in response
    assert "anxiety" in response or "sleep" in response
    assert "What part" in response


def test_fallback_handles_uncertainty_as_conversation():
    history = [{"role": "user", "content": "I feel guilty all the time"}]

    response = get_supportive_fallback("I don't know", history)

    assert "Not knowing is still an answer" in response
    assert "guilt" in response
    assert "one small thread" in response


def test_fallback_bonding_reply_invites_next_turn_without_urgent_language():
    response = get_supportive_fallback("I do not feel connected to my baby")

    assert response != CRISIS_RESOURCE_MESSAGE
    assert "bad parent" in response
    assert "one moment" in response
