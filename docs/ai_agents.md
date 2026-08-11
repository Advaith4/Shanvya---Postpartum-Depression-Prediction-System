# AI Agents

## Current CrewAI Integration

CrewAI is integrated in the chatbot flow through `crew_chatbot.py`.

The Flask `/chat` route now follows this order:

1. Try CrewAI multi-agent response.
2. If CrewAI is unavailable or not configured, use Hugging Face API.
3. If the API is unavailable, use the local supportive fallback.

## Chatbot Agents

| Agent | Role |
|---|---|
| Maternal Safety Triage Agent | Checks whether the user's message suggests crisis, distress, casual conversation, or another situation. |
| Postpartum Support Response Agent | Generates a short, warm, non-diagnostic support reply. |

## Required Configuration

CrewAI is optional at runtime. To enable it, install requirements and configure a Groq API key:

```text
CREWAI_ENABLED=true
GROQ_API_KEY=your_groq_key_here
GROQ_MODEL=groq/llama-3.1-8b-instant
```

If `GROQ_API_KEY` is missing or CrewAI is not installed, the chatbot still works using the existing fallback path.

## Good Future Agent Use Cases

| Area | Agent idea |
|---|---|
| Screening result review | Agent summarizes EPDS-proxy result, ML support signal, confidence score, and SHAP explanation in safer plain language. |
| Safety escalation | Agent checks for self-harm signals and prioritizes emergency/support resources. |
| Counselor call scheduling | Agent assigns call priority from screening severity and user message. |
| Report generation | Agent creates a clean post-screening summary for assignment or counselor review. |
| Follow-up planning | Agent suggests gentle next steps based on risk level without diagnosing. |

## Boundary

Agents must not make the final screening decision. The screening result should remain based on deterministic EPDS-proxy scoring and the trained Logistic Regression model.
