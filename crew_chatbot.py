import os
import logging

from agents import build_safety_triage_agent, build_support_response_agent
from guardrails import (
    CRISIS_RESOURCE_MESSAGE,
    ELEVATED_KEYWORDS,
    ELEVATED_RISK,
    ROUTINE_RISK,
    URGENT_KEYWORDS,
    URGENT_RISK,
    apply_output_guardrails,
    contains_any_phrase,
    contains_phrase,
    has_crisis_language,
    local_risk_level,
    normalize_text,
    validate_user_message,
)


logger = logging.getLogger(__name__)

AFFIRMATION_KEYWORDS = (
    "yes",
    "yeah",
    "yep",
    "true",
    "exactly",
    "that is it",
    "that's it",
    "correct",
    "right",
)

NEGATION_KEYWORDS = (
    "no",
    "nope",
    "not really",
    "not exactly",
    "i don't think so",
    "i do not think so",
)

UNCERTAINTY_KEYWORDS = (
    "i don't know",
    "i do not know",
    "not sure",
    "maybe",
    "confused",
    "i can't explain",
    "i cannot explain",
)

THANKS_KEYWORDS = (
    "thanks",
    "thank you",
    "okay",
    "ok",
    "fine",
)

MEMORY_KEYWORDS = (
    "remember",
    "my choices",
    "my answers",
    "what i selected",
    "what did i select",
    "previous response",
    "previous answers",
    "my result",
    "my score",
)


def _normalize(message):
    return normalize_text(message)


def _contains_phrase(message, keyword):
    return contains_phrase(message, keyword)


def _contains_any_phrase(message, keywords):
    return contains_any_phrase(message, keywords)


def _is_simple_greeting(message):
    return _normalize(message) in {
        "hi",
        "hello",
        "hey",
        "good morning",
        "good afternoon",
        "good evening",
    }


def _mentions_any(message, keywords):
    return _contains_any_phrase(message, keywords)


def _recent_user_messages(chat_history):
    return [
        item.get("content", "")
        for item in chat_history or []
        if item.get("role") == "user" and item.get("content")
    ]


def _last_assistant_message(chat_history):
    for item in reversed(chat_history or []):
        if item.get("role") == "assistant" and item.get("content"):
            return item.get("content", "")
    return ""


def _last_user_message(chat_history):
    for item in reversed(chat_history or []):
        if item.get("role") == "user" and item.get("content"):
            return item.get("content", "")
    return ""


def _conversation_turn_count(chat_history):
    return len(_recent_user_messages(chat_history))


def _screening_summary(user_context):
    if not user_context:
        return []

    lines = []
    risk_level = user_context.get("risk_level")
    epds_score = user_context.get("epds_score")
    concern_areas = user_context.get("concern_areas") or []
    notable_responses = user_context.get("notable_responses") or []

    if risk_level:
        score_text = f" with EPDS-proxy score {epds_score}/30" if epds_score is not None else ""
        lines.append(f"Screening result: {risk_level}{score_text}.")
    if concern_areas:
        lines.append(f"Screening concern areas: {', '.join(concern_areas)}.")
    if notable_responses:
        formatted = ", ".join(
            f"{item.get('label')}: {item.get('response')}"
            for item in notable_responses[:5]
            if item.get("label") and item.get("response")
        )
        if formatted:
            lines.append(f"Notable screening answers: {formatted}.")
    return lines


def build_user_context_summary(chat_history=None, user_context=None, current_msg=""):
    lines = _screening_summary(user_context)
    concerns = _known_concerns(chat_history, current_msg, user_context)
    if concerns:
        lines.append(f"Known concern areas from chat and screening: {', '.join(concerns[:5])}.")
    last_user = _last_user_message(chat_history)
    if last_user:
        lines.append(f"Previous user message: {last_user}")
    if not lines:
        return "No saved screening context yet. Use only the current chat and recent messages."
    return "\n".join(lines)


def _conversation_context(chat_history):
    lines = []
    for item in (chat_history or [])[-14:]:
        role = "User" if item.get("role") == "user" else "Assistant"
        content = item.get("content", "").strip()
        if content:
            lines.append(f"{role}: {content}")
    return "\n".join(lines) if lines else "No previous chat context."


def _known_concerns(chat_history, current_msg, user_context=None):
    text = " ".join(_recent_user_messages(chat_history) + [current_msg])
    normalized = _normalize(text)
    concerns = list((user_context or {}).get("concern_areas") or [])
    checks = (
        ("depression", ("depressed", "depression", "hopeless", "sad", "crying")),
        ("anxiety", ("anxious", "panic", "scared", "fear")),
        ("sleep difficulty", ("sleep", "sleeping", "sleepless", "tired", "exhausted", "fatigue")),
        ("guilt", ("guilt", "guilty", "worthless")),
        ("bonding difficulty", ("bond", "bonding", "baby")),
    )
    for label, keywords in checks:
        if label not in concerns and _contains_any_phrase(normalized, keywords):
            concerns.append(label)
    return concerns


def _message_intent(message):
    msg = _normalize(message)
    if _contains_any_phrase(msg, AFFIRMATION_KEYWORDS):
        return "affirming"
    if _contains_any_phrase(msg, NEGATION_KEYWORDS):
        return "correcting"
    if _contains_any_phrase(msg, UNCERTAINTY_KEYWORDS):
        return "uncertain"
    if _contains_any_phrase(msg, THANKS_KEYWORDS):
        return "closing_or_acknowledging"
    if "?" in message:
        return "asking"
    return "sharing"


def _primary_concern(concerns):
    if not concerns:
        return None
    for preferred in ("self-harm concern", "sleep difficulty", "anxiety", "depression", "guilt", "bonding difficulty"):
        if preferred in concerns:
            return preferred
    return concerns[0]


def _continuity_prefix(chat_history, concerns):
    if not chat_history:
        return ""
    primary = _primary_concern(concerns)
    if primary:
        return f"Let us stay with the {primary} you have been describing. "
    return "Let us stay with what you just shared. "


def _next_step_for_concern(primary):
    if primary == "sleep difficulty":
        return (
            "For the next few minutes, it may help to separate two things: what your body needs tonight, "
            "and who can help you get even one protected rest window."
        )
    if primary == "anxiety":
        return (
            "For this moment, try to name whether the worry is about the baby, your body, your relationship, "
            "or the day ahead. That can make the feeling less shapeless."
        )
    if primary == "depression":
        return (
            "We can take this slowly: what matters first is whether the day feels heavy because of sadness, "
            "numbness, guilt, or pure exhaustion."
        )
    if primary == "guilt":
        return (
            "Guilt can sound very convincing when you are worn down. We can look at what it is accusing you of, "
            "without treating that accusation as the truth."
        )
    if primary == "bonding difficulty":
        return (
            "Bonding can be quieter and slower than people admit. We can talk about what moments feel easiest "
            "with the baby, even if they are very small."
        )
    return (
        "We can build this conversation one piece at a time: what happened, what you felt, and what support "
        "would make the next hour easier."
    )


def get_supportive_fallback(user_msg, chat_history=None, user_context=None):
    risk_level = local_risk_level(user_msg)
    msg = _normalize(user_msg)
    concerns = _known_concerns(chat_history, user_msg, user_context)
    screening_lines = _screening_summary(user_context)
    intent = _message_intent(user_msg)
    primary = _primary_concern(concerns)
    continuity = _continuity_prefix(chat_history, concerns)
    next_step = _next_step_for_concern(primary)
    turn_count = _conversation_turn_count(chat_history)

    if risk_level == URGENT_RISK:
        return CRISIS_RESOURCE_MESSAGE
    if _mentions_any(msg, MEMORY_KEYWORDS):
        remembered = []
        if screening_lines:
            remembered.append(" ".join(screening_lines))
        if concerns:
            remembered.append(f"In this chat, the main themes I have noticed are {', '.join(concerns[:4])}.")
        if remembered:
            return "Yes. " + " ".join(remembered) + " I will use that context as we talk."
        return (
            "I can remember what you share in this chat session. I do not have saved screening choices or a result yet, "
            "so tell me what you selected or what result you saw, and I will use it as we talk."
        )
    if _contains_any_phrase(msg, ["hi", "hello", "hey", "good morning", "good evening", "good afternoon"]):
        if screening_lines:
            return (
                "Hello, I am here with you. I also have your screening context in mind, so we do not have to start from zero. "
                f"{next_step} What feels most important to talk about first?"
            )
        return (
            "Hello, I am here with you. We can take this slowly and make it a real conversation, not a checklist. "
            "Tell me what today has felt like in your body or your mood, even if it is messy."
        )
    if intent == "affirming" and chat_history:
        return (
            f"{continuity}That makes sense. I am going to follow your lead instead of jumping to advice. "
            f"{next_step} What part of that feels most intense right now?"
        )
    if intent == "correcting" and chat_history:
        return (
            "Thank you for correcting me. I do not want to force a meaning onto what you said. "
            "Tell me the closer version: is it more numb, irritated, lonely, tired, worried, or something else?"
        )
    if intent == "uncertain":
        return (
            f"{continuity}Not knowing is still an answer. Sometimes everything is tangled together after birth. "
            f"{next_step} If you had to pick one small thread, would it be your mood, sleep, worry, support at home, or the baby?"
        )
    if intent == "closing_or_acknowledging" and turn_count >= 1:
        return (
            "I am glad you are still here with me. We can keep going gently. "
            f"{next_step} You can answer with just a few words if that is easier."
        )
    if risk_level == ELEVATED_RISK:
        if _contains_any_phrase(msg, ["depressed", "depression", "hopeless", "worthless"]):
            if "sleep difficulty" in concerns:
                return (
                    f"{continuity}Feeling depressed while sleep is broken can make even ordinary tasks feel far too large. "
                    "I am not going to rush you into fixing all of it at once. "
                    "Is the hardest part the low mood itself, the lack of rest, or feeling unable to manage the day?"
                )
            return (
                f"{continuity}I am sorry you are carrying that. When you say you feel depressed, I want to understand the weight of it instead of giving you a canned answer. "
                "Is it mostly sadness, numbness, guilt, or feeling unable to cope? If this has lasted most of the day for several days, please consider speaking with a doctor, counselor, or someone you trust today."
            )
        if _contains_any_phrase(msg, ["anxious", "panic", "scared"]):
            return (
                f"{continuity}That anxious feeling can be frightening, especially when you are already tired. "
                "Before we unpack it, try naming one thing you can see and one thing you can feel under your hand. "
                "What does the worry seem to circle back to most?"
            )
        return (
            f"{continuity}That sounds heavy, and I am glad you said it out loud here. "
            f"{next_step} What would you want someone close to you to understand about this?"
        )
    if _contains_any_phrase(msg, ["tired", "sleep", "weary", "drain", "fatigue"]):
        return (
            f"{continuity}That level of tiredness can make everything feel sharper and harder. "
            "I want to understand the pattern, because each kind of tired needs a different kind of support. "
            "Is the problem falling asleep, waking often, or not getting chances to rest?"
        )
    if primary == "bonding difficulty" or _contains_any_phrase(msg, ["bond", "connected", "connection", "feel nothing"]):
        return (
            f"{continuity}Difficulty feeling connected can be painful to admit, and it does not make you a bad parent. "
            "Some parents feel love as a rush, some as duty first, and some only in tiny moments. "
            "What is one moment with the baby that feels even slightly easier than the others?"
        )
    return (
        f"{continuity}I am here with you, and I will keep track as we go. "
        f"{next_step} What happened today that made this feel important to say?"
    )


def _crewai_is_configured():
    return bool(os.environ.get("GROQ_API_KEY"))


def _build_groq_llm():
    from crewai import LLM

    return LLM(
        model=os.environ.get("GROQ_MODEL", "groq/llama-3.1-8b-instant"),
        api_key=os.environ["GROQ_API_KEY"],
        temperature=0.2,
    )


def _extract_text(result):
    return (getattr(result, "raw", None) or str(result)).strip()


def _parse_triage_risk(triage_text):
    normalized = triage_text.upper()
    if URGENT_RISK in normalized or "CRISIS" in normalized:
        return URGENT_RISK
    if ELEVATED_RISK in normalized or "DISTRESS" in normalized:
        return ELEVATED_RISK
    if ROUTINE_RISK in normalized or "CASUAL" in normalized or "OTHER" in normalized:
        return ROUTINE_RISK
    return ELEVATED_RISK


def _run_triage(user_input, chat_history, llm):
    from crewai import Crew, Process, Task

    safety_agent = build_safety_triage_agent(llm)
    triage_task = Task(
        description=(
            "Classify this postpartum support chat message into exactly one risk level: "
            "URGENT, ELEVATED, or ROUTINE.\n\n"
            "URGENT means self-harm, harm to baby/others, psychosis-like language, feeling unsafe, "
            "or immediate danger.\n"
            "ELEVATED means strong distress, hopelessness, panic, severe anxiety, or inability to cope "
            "without immediate danger.\n"
            "ROUTINE means greeting, ordinary support, or non-urgent conversation.\n\n"
            "Use recent conversation context only to understand continuity. The current user message is most important.\n\n"
            f"Recent conversation:\n{_conversation_context(chat_history)}\n\n"
            "Return format only: RISK_LEVEL: <URGENT|ELEVATED|ROUTINE>\n"
            f"User message: {user_input}"
        ),
        expected_output="RISK_LEVEL: URGENT, RISK_LEVEL: ELEVATED, or RISK_LEVEL: ROUTINE.",
        agent=safety_agent,
    )
    crew = Crew(
        agents=[safety_agent],
        tasks=[triage_task],
        process=Process.sequential,
        verbose=False,
    )
    return _parse_triage_risk(_extract_text(crew.kickoff()))


def _run_support_response(user_input, risk_level, chat_history, user_context, llm):
    from crewai import Crew, Process, Task

    support_agent = build_support_response_agent(llm)
    response_task = Task(
        description=(
            "Write one short postpartum support chatbot reply that feels like a careful human conversation.\n"
            f"Fixed risk level from safety triage: {risk_level}.\n"
            "Do not override or reclassify this risk level.\n"
            "Keep it between 90 and 150 words unless the user only greeted you or is in crisis.\n"
            "Ask exactly one gentle follow-up question for non-urgent messages. Use only one question mark.\n"
            "Do not use pet names, emojis, poetic language, or generic reassurance like 'you are strong'.\n"
            "Reflect the user's exact concern before giving advice.\n"
            "Treat every user answer as meaningful. If they say yes/no/maybe/okay, infer what they are answering from the previous assistant message and continue that thread.\n"
            "Use saved user context and recent conversation context to avoid asking repeated questions and to refer to concerns the user already shared.\n"
            "Make the conversation feel continuous: acknowledge what changed, connect it to earlier themes, offer one small stabilizing next step, then ask one specific question.\n"
            "If the user asks about memory, clearly say what you remember from this chat.\n"
            "Encourage professional or trusted human support when the risk level is ELEVATED.\n"
            "Do not name specific support organizations, hotlines, or phone numbers unless the risk level is URGENT.\n\n"
            f"Saved user context:\n{build_user_context_summary(chat_history, user_context, user_input)}\n\n"
            f"Recent conversation:\n{_conversation_context(chat_history)}\n\n"
            f"User message: {user_input}"
        ),
        expected_output="One user-facing supportive chatbot response.",
        agent=support_agent,
    )
    crew = Crew(
        agents=[support_agent],
        tasks=[response_task],
        process=Process.sequential,
        verbose=False,
    )
    return _extract_text(crew.kickoff())


def generate_crewai_chat_response(user_input, chat_history=None, user_context=None):
    input_guardrail = validate_user_message(user_input)
    if not input_guardrail.allowed:
        logger.warning("User input guardrail triggered: %s", input_guardrail.reason)
        return input_guardrail.replacement

    if _is_simple_greeting(user_input) or _mentions_any(_normalize(user_input), MEMORY_KEYWORDS):
        return apply_output_guardrails(
            get_supportive_fallback(user_input, chat_history, user_context),
            input_guardrail.risk_level,
        )

    if not os.environ.get("CREWAI_ENABLED", "true").lower() in {"1", "true", "yes"}:
        return None

    if not _crewai_is_configured():
        return None

    llm = None
    try:
        llm = _build_groq_llm()
        risk_level = _run_triage(user_input, chat_history, llm)
    except Exception as exc:
        logger.warning("CrewAI triage failed; using local risk fallback: %s", exc)
        risk_level = input_guardrail.risk_level

    if risk_level == URGENT_RISK:
        return CRISIS_RESOURCE_MESSAGE

    if llm is None:
        return apply_output_guardrails(
            get_supportive_fallback(user_input, chat_history, user_context),
            risk_level,
        )

    try:
        response = _run_support_response(user_input, risk_level, chat_history, user_context, llm)
        return apply_output_guardrails(response, risk_level)
    except Exception as exc:
        logger.warning("CrewAI support response failed; using rule fallback: %s", exc)
        return apply_output_guardrails(
            get_supportive_fallback(user_input, chat_history, user_context),
            risk_level,
        )
