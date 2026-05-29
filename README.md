# Shanvya 🌸
> **Caring for the One Who Cares.** A compassionate, private, and clinically validated digital platform built to screen for postpartum distress and guide new mothers toward healing.

Shanvya is a production-ready Flask web application that helps detect indicators of Postpartum Depression (PPD) using a machine learning classifier. The assessment questions are derived from the clinically proven **Edinburgh Postnatal Depression Scale (EPDS)**. 

If high distress indicators are detected, Shanvya seamlessly directs the mother to a secure, private counseling chatroom powered by a warm, emotionally intelligent AI counselor.

---

## 🎨 Visual Identity & Aesthetic

The platform is designed with a deeply comforting, "motherly" visual system:
* **Soothing Palette:** Gentle terracotta/rose blushes, soft ivory-cream backgrounds, and healing sage green accents.
* **Warm Gradients:** Dreamy pastel gradient flows (corals, peaches, and teals) and decorative floating background orbs that create a peaceful, therapeutic self-care space.
* **Interactive UI:** Fluid micro-interactions, floating pill-shaped glassmorphic headers, and an interactive educational tabbed interface.
* **Empathetic Onboarding:** A single-question wizard displaying one question at a time to minimize cognitive fatigue, accompanied by encouraging dynamic maternal quotes on every step.

---

## 🔬 Clinical Methodology & Machine Learning

* **Methodology:** The screening questions are grounded in the **Edinburgh Postnatal Depression Scale (EPDS)**, a widely recognized diagnostic questionnaire developed in 1987.
* **Prediction Model:** Utilizes a highly balanced **CatBoost Classifier** trained on Balanced Dataset Undersampling, achieving an **accuracy of over 96%** on clinical testing indicators.
* **Counseling Assistant:** Integrates the HuggingFace Inference API (`Mistral-7B-Instruct-v0.3`) to deliver private, highly empathetic, emotionally intelligent counselor responses, alongside immediate hotlines (AASRA, SNEHA).

---

## 🚀 How to Run Locally

### 1. Clone the repository
```bash
git clone https://github.com/Advaith4/Shanvya---Postpartum-Depression-Prediction-System.git
cd Shanvya---Postpartum-Depression-Prediction-System
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set your HuggingFace API key
To enable the AI counselor chatbot, set your HuggingFace token in your environment:
* **Windows Command Prompt:** `set HF_TOKEN=your_token_here`
* **Windows PowerShell:** `$env:HF_TOKEN="your_token_here"`
* **Linux/macOS:** `export HF_TOKEN="your_token_here"`

### 4. (Optional) Retrain the model
The pre-trained model is already included as `catboostmodel_balanced.joblib`. If you wish to retrain it:
```bash
python train_model.py
```

### 5. Launch the application
```bash
python app.py
```
Open your browser and navigate to **http://localhost:5001**.

---

## ☁️ Deployment

### Render (Recommended)
1. Link your GitHub repository to [Render](https://render.com/).
2. Select **Web Service** and choose **Python** environment.
3. Configure the following:
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `gunicorn app:app`
4. Add an **Environment Variable**: `HF_TOKEN` = `your_huggingface_token`.

### Vercel
This project includes a native `vercel.json` configuration file. Just link your GitHub repository to Vercel, add your `HF_TOKEN` environment variable, and hit deploy!
