import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from preprocess_dataset import CATBOOST_READY_DATA_PATH, EXPECTED_COLUMNS


MODEL_NAME = "logistic_regression"
MODEL_PATH = Path("models/ppd_logistic_regression.joblib")
METADATA_PATH = Path("models/ppd_logistic_regression_metadata.json")
MODEL_THRESHOLD = 0.35

IMPUTATION_VALUES = {
    "Irritable towards baby & partner": "Yes",
    "Problems concentrating or making decision": "No",
    "Feeling of guilt": "No",
}

_SHAP_CACHE = {}


class ModelInputError(ValueError):
    pass


def load_model_bundle():
    if not MODEL_PATH.exists() or not METADATA_PATH.exists():
        raise FileNotFoundError("Logistic Regression model artifacts not found. Run 'python train_logistic_model.py'.")
    model = joblib.load(MODEL_PATH)
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    return model, metadata


def validate_features(features):
    missing_features = [feature for feature in EXPECTED_COLUMNS if feature not in features]
    if missing_features:
        raise ModelInputError(f"Missing required feature(s): {', '.join(missing_features)}")

    validated = {}
    for feature in EXPECTED_COLUMNS:
        value = features.get(feature)
        if pd.isna(value) or value == "":
            if feature in IMPUTATION_VALUES:
                value = IMPUTATION_VALUES[feature]
            else:
                raise ModelInputError(f"Missing value for required feature: {feature}")
        validated[feature] = str(value)
    return pd.DataFrame([validated], columns=EXPECTED_COLUMNS)


def _parse_encoded_feature(encoded_feature_name):
    clean_name = encoded_feature_name.replace("categorical__", "", 1)
    for feature in EXPECTED_COLUMNS:
        prefix = f"{feature}_"
        if clean_name.startswith(prefix):
            return feature, clean_name[len(prefix):]
    return clean_name, ""


def explain_prediction(features, model):
    if not hasattr(model, "named_steps"):
        return []

    input_data = validate_features(features)
    transformed = model.named_steps["preprocess"].transform(input_data)
    coefficients = model.named_steps["model"].coef_[0]
    encoded_names = model.named_steps["preprocess"].get_feature_names_out()

    if hasattr(transformed, "tocoo"):
        active_indices = transformed.tocoo().col
    else:
        active_indices = [index for index, value in enumerate(transformed[0]) if value]

    contributions = []
    for index in active_indices:
        coefficient = float(coefficients[index])
        feature, response = _parse_encoded_feature(encoded_names[index])
        contributions.append(
            {
                "feature": feature,
                "response": response,
                "direction": "increases_support_signal" if coefficient >= 0 else "decreases_support_signal",
                "importance": abs(coefficient),
            }
        )

    return sorted(contributions, key=lambda item: item["importance"], reverse=True)[:4]


def explain_prediction_with_shap(features, model):
    try:
        import shap
    except ImportError:
        return []

    if not hasattr(model, "named_steps") or not CATBOOST_READY_DATA_PATH.exists():
        return []

    input_data = validate_features(features)

    preprocess = model.named_steps["preprocess"]
    classifier = model.named_steps["model"]
    transformed_input = preprocess.transform(input_data)

    if hasattr(transformed_input, "toarray"):
        transformed_input = transformed_input.toarray()

    cache_key = str(MODEL_PATH.resolve())
    cached = _SHAP_CACHE.get(cache_key)
    if cached is None:
        background = pd.read_csv(CATBOOST_READY_DATA_PATH)[EXPECTED_COLUMNS].astype(str)
        transformed_background = preprocess.transform(background)
        if hasattr(transformed_background, "toarray"):
            transformed_background = transformed_background.toarray()
        cached = {
            "explainer": shap.LinearExplainer(classifier, transformed_background),
            "encoded_names": preprocess.get_feature_names_out(),
        }
        _SHAP_CACHE[cache_key] = cached

    explainer = cached["explainer"]
    shap_values = explainer.shap_values(transformed_input)
    if isinstance(shap_values, list):
        shap_values = shap_values[1]

    shap_values = np.asarray(shap_values)[0]
    coefficients = classifier.coef_[0]
    encoded_names = cached["encoded_names"]
    active_indices = [index for index, value in enumerate(transformed_input[0]) if value]

    contributions = []
    for index in active_indices:
        feature, response = _parse_encoded_feature(encoded_names[index])
        shap_value = float(shap_values[index])
        coefficient = float(coefficients[index])
        contributions.append(
            {
                "feature": feature,
                "response": response,
                "shap_value": shap_value,
                "abs_shap_value": abs(shap_value),
                "direction": "increases_support_signal" if coefficient >= 0 else "decreases_support_signal",
            }
        )

    return sorted(contributions, key=lambda item: item["abs_shap_value"], reverse=True)[:4]


def predict_support_signal(features, model=None, metadata=None):
    if model is None or metadata is None:
        model, metadata = load_model_bundle()

    input_data = validate_features(features)
    threshold = float(metadata.get("threshold", MODEL_THRESHOLD))
    probability = float(model.predict_proba(input_data)[0][1])
    predicted_label = int(probability >= threshold)
    contributions = explain_prediction(features, model)
    shap_contributions = explain_prediction_with_shap(features, model)

    return {
        "model_name": metadata.get("model_name", MODEL_NAME),
        "predicted_label": predicted_label,
        "probability": probability,
        "threshold": threshold,
        "support_signal": "Elevated" if predicted_label == 1 else "Not elevated",
        "explanation_method": "local_shap_with_logistic_coefficient_direction",
        "top_contributions": contributions,
        "local_shap_contributions": shap_contributions,
    }


def model_support_band(probability, threshold):
    margin = probability - threshold
    if margin >= 0.20:
        return "Strong ML support for elevated proxy-risk pattern"
    if margin >= 0:
        return "Moderate ML support for elevated proxy-risk pattern"
    if margin >= -0.10:
        return "Borderline ML support signal"
    return "Low ML support for elevated proxy-risk pattern"
