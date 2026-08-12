import re
from dataclasses import dataclass


URGENT_RISK = "URGENT"
ELEVATED_RISK = "ELEVATED"
ROUTINE_RISK = "ROUTINE"

CRISIS_RESOURCE_MESSAGE = (
    "I am really sorry you are feeling this much pain. Please seek immediate human support now. "
    "If you are in India, you can contact AASRA (91-22-27546669) or SNEHA (91-44-24640050), "
    "or reach local emergency services. Please also tell a trusted person near you right now. "
    "You do not have to handle this alone."
)

SAFE_FALLBACK_MESSAGE = (
    "I am here with you. I want to respond carefully and safely, so let us slow this down. "
    "Tell me what feels most difficult right now, and if this feels urgent or unsafe, please reach out to a trusted person or emergency support near you."
)

URGENT_KEYWORDS = (
    "suicide",
    "suicidal",
    "kill myself",
    "end my life",
    "want to die",
    "wish i was dead",
    "self harm",
    "self-harm",
    "harm myself",
    "hurt myself",
    "overdose",
    "harm my baby",
    "hurt my baby",
    "kill my baby",
    "baby is not safe",
    "voices",
    "hearing voices",
    "seeing things",
    "not real",
    "losing my mind",
    "out of control",
)

ELEVATED_KEYWORDS = (
    "depressed",
    "depression",
    "crying",
    "hopeless",
    "panic",
    "anxious",
    "scared",
    "worthless",
    "guilt",
    "can't cope",
    "cannot cope",
    "exhausted",
    "no sleep",
)

FORBIDDEN_DIAGNOSIS_PATTERNS = (
    r"\byou have (?:ppd|postpartum depression|depression|anxiety|psychosis)\b",
    r"\byou are diagnosed\b",
    r"\byou(?:'re| are) clinically diagnosed\b",
    r"\bthis confirms\b",
    r"\bdefinitely (?:ppd|postpartum depression|depression|anxiety|psychosis)\b",
)

FORBIDDEN_MEDICAL_ADVICE_PATTERNS = (
    r"\btake \d+\s*(?:mg|milligrams?)\b",
    r"\b(?:increase|decrease|stop|start|double|skip) (?:your )?(?:dose|dosage|medication|medicine|antidepressant)\b",
    r"\b(?:prescribe|prescription)\b",
    r"\b(?:sertraline|fluoxetine|prozac|zoloft|lexapro|escitalopram)\b",
)

NON_URGENT_HOTLINE_PATTERNS = (
    r"\bpostpartum support international\b",
    r"\baasra\b",
    r"\bsneha\b",
    r"\b\d{2,}[-\s]\d{2,}[-\s]\d{4,}\b",
)


@dataclass(frozen=True)
class GuardrailResult:
    allowed: bool
    risk_level: str
    reason: str = ""
    replacement: str | None = None


def normalize_text(text):
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def contains_phrase(message, keyword):
    pattern = r"(?<![a-z0-9])" + re.escape(keyword) + r"(?![a-z0-9])"
    return re.search(pattern, message) is not None


def contains_any_phrase(message, keywords):
    normalized = normalize_text(message)
    return any(contains_phrase(normalized, keyword) for keyword in keywords)


def has_crisis_language(message):
    return contains_any_phrase(message, URGENT_KEYWORDS)


def local_risk_level(message):
    if has_crisis_language(message):
        return URGENT_RISK
    if contains_any_phrase(message, ELEVATED_KEYWORDS):
        return ELEVATED_RISK
    return ROUTINE_RISK


def validate_user_message(message):
    risk_level = local_risk_level(message)
    if risk_level == URGENT_RISK:
        return GuardrailResult(
            allowed=False,
            risk_level=URGENT_RISK,
            reason="urgent_user_language",
            replacement=CRISIS_RESOURCE_MESSAGE,
        )
    return GuardrailResult(allowed=True, risk_level=risk_level)


def _matches_any_pattern(text, patterns):
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def validate_bot_response(response, risk_level=ROUTINE_RISK):
    text = response or ""
    if not text.strip():
        return GuardrailResult(
            allowed=False,
            risk_level=risk_level,
            reason="empty_response",
            replacement=SAFE_FALLBACK_MESSAGE,
        )
    if _matches_any_pattern(text, FORBIDDEN_DIAGNOSIS_PATTERNS):
        return GuardrailResult(
            allowed=False,
            risk_level=risk_level,
            reason="diagnosis_claim",
            replacement=SAFE_FALLBACK_MESSAGE,
        )
    if _matches_any_pattern(text, FORBIDDEN_MEDICAL_ADVICE_PATTERNS):
        return GuardrailResult(
            allowed=False,
            risk_level=risk_level,
            reason="medical_advice",
            replacement=SAFE_FALLBACK_MESSAGE,
        )
    if risk_level != URGENT_RISK and _matches_any_pattern(text, NON_URGENT_HOTLINE_PATTERNS):
        return GuardrailResult(
            allowed=False,
            risk_level=risk_level,
            reason="non_urgent_hotline",
            replacement=SAFE_FALLBACK_MESSAGE,
        )
    return GuardrailResult(allowed=True, risk_level=risk_level)


def apply_output_guardrails(response, risk_level=ROUTINE_RISK):
    result = validate_bot_response(response, risk_level)
    return response if result.allowed else result.replacement
