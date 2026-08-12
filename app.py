import os

import pandas as pd
import requests
from dotenv import load_dotenv
from flask import Flask, request, render_template, jsonify, redirect, url_for, session
from flask_cors import CORS

from crew_chatbot import (
    build_user_context_summary,
    generate_crewai_chat_response,
    get_supportive_fallback,
)
from guardrails import apply_output_guardrails, local_risk_level, validate_user_message
from ml_inference import (
    ModelInputError,
    load_model_bundle,
    model_support_band,
    predict_support_signal,
)


# -----------------
# App Initialization
# -----------------
load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "shanvya-dev-secret-key")
CORS(app)

def model_confidence_score(probability, threshold):
    if threshold <= 0 or threshold >= 1:
        return round(probability * 100, 1)

    if probability >= threshold:
        normalized_distance = (probability - threshold) / (1 - threshold)
    else:
        normalized_distance = (threshold - probability) / threshold

    return round(max(0, min(1, normalized_distance)) * 100, 1)


def confidence_label(confidence):
    if confidence >= 70:
        return "High model certainty for this support signal"
    if confidence >= 40:
        return "Moderate model certainty for this support signal"
    return "Borderline model certainty; interpret with extra caution"


def user_facing_explanation_items(support_signal):
    shap_items = support_signal.get("local_shap_contributions", [])
    fallback_items = support_signal.get("top_contributions", [])
    items = shap_items or fallback_items
    if not items:
        return [], "What influenced this result"

    if support_signal.get("predicted_label") == 1:
        filtered = [
            item for item in items
            if item.get("direction") == "increases_support_signal"
        ]
        return (filtered or items)[:4], "What raised this support signal"

    filtered = [
        item for item in items
        if item.get("direction") == "decreases_support_signal"
    ]
    return (filtered or items)[:4], "What lowered this support signal"


try:
    model, model_metadata = load_model_bundle()
    feature_columns = model_metadata["features"]
    decision_threshold = model_metadata["threshold"]
    print("Model loaded successfully.")
except (FileNotFoundError, OSError):
    print("Model not found! Please run 'python train_logistic_model.py' first.")
    model = None
    model_metadata = {}
    feature_columns = []
    decision_threshold = 0.35

questions = [
    {
        "text": "What is your age range?",
        "options": ["25-30", "30-35", "35-40", "40-45", "45-50"],
    },
    {
        "text": "Do you often feel sad or tearful?",
        "options": ["Yes", "No", "Sometimes"],
    },
    {
        "text": "Do you feel irritable towards your baby or partner?",
        "options": ["Yes", "No", "Sometimes"],
    },
    {
        "text": "Do you have trouble sleeping at night?",
        "options": ["Two or more days a week", "Yes", "No"],
    },
    {
        "text": "Do you have problems concentrating or making decisions?",
        "options": ["Often", "Yes", "No"],
    },
    {
        "text": "Have you experienced overeating or loss of appetite?",
        "options": ["Yes", "No", "Not at all"],
    },
    {
        "text": "Do you often feel anxious?",
        "options": ["Yes", "No"],
    },
    {
        "text": "Do you feel a sense of guilt?",
        "options": ["Yes", "No", "Maybe"],
    },
    {
        "text": "Are you having problems bonding with your baby?",
        "options": ["Yes", "No", "Sometimes"],
    },
    {
        "text": "Have you ever attempted or thought about suicide?",
        "options": ["Yes", "No", "Not interested to say"],
    },
]


EPDS_PROXY_SCORE_MAPS = {
    "Feeling sad or Tearful": {"No": 0, "Sometimes": 2, "Yes": 3},
    "Irritable towards baby & partner": {"No": 0, "Sometimes": 2, "Yes": 3},
    "Trouble sleeping at night": {"No": 0, "Yes": 2, "Two or more days a week": 3},
    "Problems concentrating or making decision": {"No": 0, "Yes": 2, "Often": 3},
    "Feeling anxious": {"No": 0, "Yes": 3},
    "Feeling of guilt": {"No": 0, "Maybe": 2, "Yes": 3},
    "Problems of bonding with baby": {"No": 0, "Sometimes": 2, "Yes": 3},
    "Suicide attempt": {"No": 0, "Not interested to say": 1, "Yes": 3},
}

CONCERN_LABELS = {
    "Feeling sad or Tearful": "sadness or tearfulness",
    "Irritable towards baby & partner": "irritability",
    "Trouble sleeping at night": "sleep difficulty",
    "Problems concentrating or making decision": "concentration or decision difficulty",
    "Feeling anxious": "anxiety",
    "Feeling of guilt": "guilt",
    "Problems of bonding with baby": "bonding difficulty",
    "Suicide attempt": "self-harm concern",
}


def build_screening_context(features, epds_result):
    notable_responses = []
    for column, label in CONCERN_LABELS.items():
        response = features.get(column)
        score = EPDS_PROXY_SCORE_MAPS[column].get(response, 0)
        if score >= 2:
            notable_responses.append({"label": label, "response": response})

    return {
        "risk_level": epds_result["risk_level"],
        "epds_score": epds_result["score_0_30"],
        "concern_areas": epds_result["concern_areas"],
        "notable_responses": notable_responses,
    }


def calculate_epds_proxy(features):
    scored_features = {
        column: EPDS_PROXY_SCORE_MAPS[column].get(features.get(column), 0)
        for column in EPDS_PROXY_SCORE_MAPS
    }
    raw_score = sum(scored_features.values())
    score_0_30 = round(raw_score / 24 * 30)

    if features.get("Suicide attempt") == "Yes":
        risk_level = "Immediate attention recommended"
    elif score_0_30 >= 13:
        risk_level = "High postpartum distress risk"
    elif score_0_30 >= 10:
        risk_level = "Moderate postpartum distress risk"
    else:
        risk_level = "Low postpartum distress risk"

    concern_areas = [
        CONCERN_LABELS[column]
        for column, score in sorted(scored_features.items(), key=lambda item: item[1], reverse=True)
        if score >= 2
    ][:4]

    return {
        "raw_score": raw_score,
        "score_0_30": score_0_30,
        "risk_level": risk_level,
        "concern_areas": concern_areas,
    }


def preprocess_responses(responses):
    if not model:
        raise Exception("Model is not loaded.")
    if len(responses) != len(feature_columns):
        raise ValueError("Please answer every question before submitting.")

    features = dict(zip(feature_columns, responses))
    return pd.DataFrame([features], columns=feature_columns)


def render_screening_error(message, status_code=400):
    return render_template("test.html", questions=questions, error_message=message), status_code


def save_chat_turn(chat_history, user_input, assistant_response):
    chat_history.append({"role": "user", "content": user_input})
    chat_history.append({"role": "assistant", "content": assistant_response})
    session["chat_history"] = chat_history[-30:]


@app.route("/")
def home():
    return render_template("home.html")

@app.route("/test", methods=["GET", "POST"])
def test():
    if request.method == "POST":
        try:
            if not model:
                return render_screening_error(
                    "The screening-support model is temporarily unavailable. Please try again later.",
                    503,
                )
                
            responses = [request.form.get(f"q-{i}") for i in range(len(questions))]
            input_data = preprocess_responses(responses)
            features = input_data.iloc[0].to_dict()
            epds_result = calculate_epds_proxy(features)
            support_signal = predict_support_signal(features, model, model_metadata)
            probability = support_signal["probability"]
            threshold = support_signal["threshold"]
            support_band = model_support_band(probability, threshold)
            confidence = model_confidence_score(probability, threshold)
            explanation_items, explanation_heading = user_facing_explanation_items(support_signal)
            session["screening_context"] = build_screening_context(features, epds_result)

            return render_template(
                "test.html",
                questions=questions,
                prediction=epds_result["risk_level"],
                epds_score=epds_result["score_0_30"],
                raw_score=epds_result["raw_score"],
                concern_areas=epds_result["concern_areas"],
                probability=round(probability * 100, 1),
                decision_threshold=round(threshold * 100, 1),
                model_confidence=confidence,
                confidence_label=confidence_label(confidence),
                ml_support_signal=support_signal["support_signal"],
                support_band=support_band,
                top_contributions=support_signal["top_contributions"],
                explanation_items=explanation_items,
                explanation_heading=explanation_heading,
                explanation_method=support_signal.get("explanation_method"),
                validation_method=model_metadata.get("validation_method"),
            )
        except ModelInputError as e:
            return render_screening_error(
                f"Unable to process the screening responses. {e}",
                400,
            )
        except Exception as e:
            return render_screening_error(
                "Unable to process the screening responses. Please check the required fields and try again.",
                500,
            )
    else:
        return render_template("test.html", questions=questions)

@app.route("/chat", methods=["GET"])
def chat():
    session.pop("chat_history", None)
    return render_template("chat.html")

@app.route("/chat/reset", methods=["POST"])
def reset_chat():
    session.pop("chat_history", None)
    return jsonify({"status": "reset"})

@app.route("/chat", methods=["POST"])
def chat_response():
    user_input = (request.json or {}).get("message", "").strip()
    if not user_input:
        return jsonify({"response": "I'm here when you're ready to talk."})

    chat_history = session.get("chat_history", [])
    user_context = session.get("screening_context", {})
    input_guardrail = validate_user_message(user_input)
    if not input_guardrail.allowed:
        final_response = input_guardrail.replacement
        save_chat_turn(chat_history, user_input, final_response)
        return jsonify({"response": final_response, "guardrail": input_guardrail.reason})

    crew_response = generate_crewai_chat_response(user_input, chat_history, user_context)
    if crew_response:
        save_chat_turn(chat_history, user_input, crew_response)
        return jsonify({"response": crew_response, "source": "crewai"})

    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        # Graceful warm fallback instead of raw configuration error
        final_response = get_supportive_fallback(user_input, chat_history, user_context)
        save_chat_turn(chat_history, user_input, final_response)
        return jsonify({"response": final_response})

    prompt = f"""
You are a warm, emotionally intelligent counselor supporting users through conversation.

Your behavior depends on the user's input:
- If the message is casual (like "hi", "hello", "good morning", etc.), respond casually and supportively.
- If the user expresses emotional distress, analyze the emotional tone and reply empathetically.
- Avoid assuming sadness unless the user explicitly or clearly shows it.
- Maintain natural, conversational tone like a real human.
- Use the saved user context and recent conversation before answering. Do not ask for information the user already gave.
- Treat every answer as meaningful. If the user says yes, no, maybe, okay, or I don't know, infer what they are replying to from the recent conversation and continue naturally.
- Write 5-8 short sentences for emotional messages. Connect to earlier themes, offer one small next step, and ask exactly one specific follow-up question.

If the user expresses suicidal thoughts or crisis, suggest contacting Indian mental health helplines like AASRA (91-22-27546669) or SNEHA (91-44-24640050).

Saved user context:
{build_user_context_summary(chat_history, user_context, user_input)}

Recent conversation:
{chr(10).join(f"{item.get('role', 'user')}: {item.get('content', '')}" for item in chat_history[-14:]) or "No previous chat context."}

User: {user_input}
Counselor:"""

    headers = {
        "Authorization": f"Bearer {hf_token}"
    }

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 250,
            "temperature": 0.7,
            "top_p": 0.95,
            "repetition_penalty": 1.2
        }
    }

    try:
        response = requests.post(
            "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        response_json = response.json()

        if isinstance(response_json, list) and 'generated_text' in response_json[0]:
            generated_text = response_json[0]['generated_text']
            final_response = generated_text.split("Counselor:", 1)[-1].strip()
        else:
            final_response = get_supportive_fallback(user_input, chat_history, user_context)

        final_response = apply_output_guardrails(final_response, local_risk_level(user_input))
        save_chat_turn(chat_history, user_input, final_response)

        return jsonify({"response": final_response})

    except Exception:
        # Always fall back to a warm, supportive, rule-based counselor message if network fails
        final_response = get_supportive_fallback(user_input, chat_history, user_context)
        final_response = apply_output_guardrails(final_response, local_risk_level(user_input))
        save_chat_turn(chat_history, user_input, final_response)
        return jsonify({"response": final_response})

if __name__ == "__main__":
    app.run(port=5001, debug=True)

