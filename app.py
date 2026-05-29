import os
import joblib
import pandas as pd
import requests
from flask import Flask, request, render_template, jsonify, redirect, url_for
from flask_cors import CORS


# -----------------
# App Initialization
# -----------------
app = Flask(__name__)
CORS(app)

# Attempt to load model
try:
    model = joblib.load("models/catboostmodel_balanced.joblib")
    print("Model loaded successfully.")
except FileNotFoundError:
    print("Model not found! Please run 'python train_model.py' first.")
    model = None

questions = [
    "Do you have problems concentrating or making decisions?",
    "Have you experienced overeating or loss of appetite?",
    "Do you often feel anxious?",
    "Do you feel a sense of guilt? (Yes/No/Maybe)",
    "Are you having problems bonding with your baby? (Yes/No/Sometimes)",
    "Have you ever attempted or thought about suicide?",
    "Do you have trouble sleeping?",
    "Do you often feel sad or hopeless? (Yes/No/Sometimes)",
    "Do you feel irritable towards your baby or partner? (Yes/No/Sometimes)"
]

def preprocess_responses(responses):
    if not model:
        raise Exception("Model is not loaded.")
        
    features = {col: 0 for col in model.feature_names_}
    
    mappings = [
        ("Problems concentrating or making decision_Yes", responses[0] if len(responses)>0 else None),
        ("Overeating or loss of appetite_Yes", responses[1] if len(responses)>1 else None),
        ("Feeling anxious_Yes", responses[2] if len(responses)>2 else None),
        ("Feeling of guilt_Yes", responses[3] if len(responses)>3 and responses[3] == "Yes" else None),
        ("Feeling of guilt_Maybe", responses[3] if len(responses)>3 and responses[3] == "Maybe" else None),
        ("Problems of bonding with baby_Yes", responses[4] if len(responses)>4 and responses[4] == "Yes" else None),
        ("Problems of bonding with baby_Sometimes", responses[4] if len(responses)>4 and (responses[4] == "Sometimes" or responses[4] == "Maybe") else None),
        ("Suicide attempt_Yes", responses[5] if len(responses)>5 else None),
        ("Trouble sleeping at night_Yes", responses[6] if len(responses)>6 else None),
        ("Feeling sad or Tearful_Yes", responses[7] if len(responses)>7 and responses[7] == "Yes" else None),
        ("Feeling sad or Tearful_Sometimes", responses[7] if len(responses)>7 and (responses[7] == "Sometimes" or responses[7] == "Maybe") else None),
        ("Irritable towards baby & partner_Yes", responses[8] if len(responses)>8 and responses[8] == "Yes" else None),
        ("Irritable towards baby & partner_Sometimes", responses[8] if len(responses)>8 and (responses[8] == "Sometimes" or responses[8] == "Maybe") else None)
    ]

    for feature_name, condition in mappings:
        if condition == "Yes" and feature_name in features:
            features[feature_name] = 1

    return pd.DataFrame([features])[model.feature_names_]


@app.route("/")
def home():
    return render_template("home.html")

@app.route("/test", methods=["GET", "POST"])
def test():
    if request.method == "POST":
        try:
            if not model:
                return "Error: Model not loaded. Train the model first."
                
            responses = [request.form.get(f"q-{i}") for i in range(9)]
            input_data = preprocess_responses(responses)
            prediction = model.predict(input_data)[0]
            result = "Positive for Postpartum Depression (PPD)" if prediction == 1 else "Negative for Postpartum Depression (PPD)"

            return render_template("test.html", questions=questions, prediction=result)
        except Exception as e:
            return f"Error processing form: {e}"
    else:
        return render_template("test.html", questions=questions)

@app.route("/chat", methods=["GET"])
def chat():
    return render_template("chat.html")

@app.route("/chat", methods=["POST"])
def chat_response():
    user_input = request.json.get("message", "").strip()
    if not user_input:
        return jsonify({"response": "I'm here when you're ready to talk. 😊"})

    # Empathy-driven fallback system when network/API is offline or failing
    def get_supportive_fallback(user_msg):
        msg = user_msg.lower()
        if any(w in msg for w in ["suicide", "kill", "die", "end my life", "harm"]):
            return "Dear mother, please know that you are not alone and there is deep care available for you. Although my connection to the AI core is currently resting, please reach out immediately to AASRA (91-22-27546669) or SNEHA (91-44-24640050). They are there to listen and hold space for you. Your life is precious. ❤️"
        if any(w in msg for w in ["hi", "hello", "hey", "good morning", "good evening", "good afternoon"]):
            return "Hello there, sweet mother. I am having a tiny connection issue with my AI core, but I wanted to immediately send a warm hug your way. How are you and your little one feeling today? ❤️"
        if any(w in msg for w in ["sad", "depressed", "cry", "crying", "anxious", "scared", "fear", "hurt"]):
            return "I can feel how heavy things are for you right now, and I am sending you so much love. Although I'm experiencing a brief network hiccup, please know that your feelings are completely valid and it is okay to not be okay. Try to take slow, gentle breaths. You are doing the best you can, and that is more than enough. 🌸"
        if any(w in msg for w in ["tired", "exhausted", "sleep", "weary", "drain", "fatigue"]):
            return "Being a mother is beautiful, but it is also incredibly exhausting. Please let yourself rest without guilt. I am having a temporary connection issue, but I want you to remember that taking care of yourself is part of taking care of your baby. Sleep, rest, and be gentle with yourself. 💤"
        return "I am right here with you. I'm currently having a small connection difficulty with my server, but I want you to know you are doing an incredibly beautiful job. Take a deep, gentle breath. You are never alone, and your feelings matter. 🌸"

    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        # Graceful warm fallback instead of raw configuration error
        return jsonify({"response": get_supportive_fallback(user_input)})

    prompt = f"""
You are a warm, emotionally intelligent counselor supporting users through conversation.

Your behavior depends on the user's input:
- If the message is casual (like "hi", "hello", "good morning", etc.), respond casually and supportively.
- If the user expresses emotional distress, analyze the emotional tone and reply empathetically.
- Avoid assuming sadness unless the user explicitly or clearly shows it.
- Maintain natural, conversational tone like a real human.

If the user expresses suicidal thoughts or crisis, suggest contacting Indian mental health helplines like AASRA (91-22-27546669) or SNEHA (91-44-24640050).

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
            final_response = get_supportive_fallback(user_input)

        return jsonify({"response": final_response})

    except Exception:
        # Always fall back to a warm, supportive, rule-based counselor message if network fails
        return jsonify({"response": get_supportive_fallback(user_input)})

if __name__ == "__main__":
    app.run(port=5001, debug=True)
