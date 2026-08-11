import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

try:
    import shap
except ImportError as exc:
    raise ImportError(
        "SHAP is required to generate explainability reports. "
        "Install dependencies with 'pip install -r requirements.txt'."
    ) from exc

from ml_inference import METADATA_PATH, MODEL_PATH
from preprocess_dataset import CATBOOST_READY_DATA_PATH, EXPECTED_COLUMNS
from train_logistic_model import TARGET


REPORTS_DIR = Path("reports")
SHAP_GLOBAL_IMPORTANCE_PATH = REPORTS_DIR / "shap_global_importance.csv"
SHAP_SUMMARY_PATH = REPORTS_DIR / "shap_summary.json"
SHAP_VALIDATION_REPORT_PATH = REPORTS_DIR / "shap_validation_report.md"


def parse_encoded_feature(encoded_feature_name):
    clean_name = encoded_feature_name.replace("categorical__", "", 1)
    for feature in EXPECTED_COLUMNS:
        prefix = f"{feature}_"
        if clean_name.startswith(prefix):
            return feature, clean_name[len(prefix) :]
    return clean_name, ""


def load_inputs():
    if not CATBOOST_READY_DATA_PATH.exists():
        raise FileNotFoundError(f"Processed dataset not found: {CATBOOST_READY_DATA_PATH}")
    if not MODEL_PATH.exists() or not METADATA_PATH.exists():
        raise FileNotFoundError("Model artifacts not found. Run 'python train_logistic_model.py'.")

    df = pd.read_csv(CATBOOST_READY_DATA_PATH)
    missing_columns = [column for column in [*EXPECTED_COLUMNS, TARGET] if column not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing expected columns: {missing_columns}")

    model = joblib.load(MODEL_PATH)
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    return df, model, metadata


def build_shap_frame(model, X):
    preprocess = model.named_steps["preprocess"]
    classifier = model.named_steps["model"]

    transformed = preprocess.transform(X)
    if hasattr(transformed, "toarray"):
        transformed = transformed.toarray()

    feature_names = preprocess.get_feature_names_out()
    explainer = shap.LinearExplainer(classifier, transformed)
    shap_values = explainer.shap_values(transformed)

    if isinstance(shap_values, list):
        shap_values = shap_values[1]

    shap_values = np.asarray(shap_values)
    mean_abs_shap = np.abs(shap_values).mean(axis=0)
    mean_shap = shap_values.mean(axis=0)
    coefficients = classifier.coef_[0]

    rows = []
    for index, encoded_name in enumerate(feature_names):
        source_feature, response_value = parse_encoded_feature(encoded_name)
        coefficient = float(coefficients[index])
        rows.append(
            {
                "encoded_feature": encoded_name,
                "source_feature": source_feature,
                "response_value": response_value,
                "mean_abs_shap": float(mean_abs_shap[index]),
                "mean_shap": float(mean_shap[index]),
                "model_coefficient": coefficient,
                "coefficient_direction": "pushes_toward_elevated_support_signal"
                if coefficient >= 0
                else "pushes_toward_lower_support_signal",
            }
        )

    return pd.DataFrame(rows).sort_values("mean_abs_shap", ascending=False)


def aggregate_to_survey_features(shap_frame):
    grouped = (
        shap_frame.groupby("source_feature", as_index=False)
        .agg(
            mean_abs_shap=("mean_abs_shap", "sum"),
            mean_shap=("mean_shap", "sum"),
        )
        .sort_values("mean_abs_shap", ascending=False)
    )
    return grouped


def write_markdown_report(metadata, df, encoded_importance, survey_importance):
    class_distribution = df[TARGET].value_counts().sort_index().astype(int).to_dict()
    top_encoded = encoded_importance.head(10)
    top_survey = survey_importance.head(10)

    lines = [
        "# SHAP Explainability Report",
        "",
        "## Scope",
        "",
        "This report explains the saved Logistic Regression screening-support model using SHAP.",
        "SHAP is used offline for model audit and documentation. The live Flask app keeps using fast coefficient-based explanations.",
        "",
        "## Model",
        "",
        f"- Model: `{metadata.get('model_name', 'logistic_regression')}`",
        f"- Artifact: `{metadata.get('artifact_path', MODEL_PATH)}`",
        f"- Dataset: `{CATBOOST_READY_DATA_PATH}`",
        f"- Rows explained: `{len(df)}`",
        f"- Target: `{TARGET}`",
        f"- Class distribution: `{class_distribution}`",
        "",
        "## Top Survey Features",
        "",
        "| Rank | Feature | Mean absolute SHAP |",
        "| --- | --- | ---: |",
    ]

    for rank, row in enumerate(top_survey.itertuples(index=False), start=1):
        lines.append(
            f"| {rank} | {row.source_feature} | {row.mean_abs_shap:.6f} |"
        )

    lines.extend(
        [
            "",
            "## Top Encoded Response Features",
            "",
            "| Rank | Survey feature | Response | Mean absolute SHAP | Model coefficient direction |",
            "| --- | --- | --- | ---: | --- |",
        ]
    )

    for rank, row in enumerate(top_encoded.itertuples(index=False), start=1):
        lines.append(
            f"| {rank} | {row.source_feature} | {row.response_value} | "
            f"{row.mean_abs_shap:.6f} | {row.coefficient_direction} |"
        )

    lines.extend(
        [
            "",
            "Mean absolute SHAP is used for importance. Direction is shown from the trained Logistic Regression coefficient because one-hot SHAP values are baseline-centered and their dataset mean can be misleading as a direction label.",
            "",
            "## Interpretation Safety",
            "",
            "SHAP values describe how this trained model uses survey responses. They are not medical causes, clinical explanations, or diagnostic evidence.",
            "The model target is an EPDS-style proxy label, so these explanations reflect the proxy labeling rule and the available dataset.",
        ]
    )

    SHAP_VALIDATION_REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    REPORTS_DIR.mkdir(exist_ok=True)
    df, model, metadata = load_inputs()
    X = df[EXPECTED_COLUMNS].astype(str)

    encoded_importance = build_shap_frame(model, X)
    survey_importance = aggregate_to_survey_features(encoded_importance)

    encoded_importance.to_csv(SHAP_GLOBAL_IMPORTANCE_PATH, index=False)

    summary = {
        "explanation_method": "SHAP LinearExplainer on trained Logistic Regression pipeline output",
        "runtime_usage": "offline_report_only",
        "model_artifact": str(MODEL_PATH),
        "dataset": str(CATBOOST_READY_DATA_PATH),
        "rows_explained": int(len(df)),
        "features": EXPECTED_COLUMNS,
        "target": TARGET,
        "class_distribution": df[TARGET].value_counts().sort_index().astype(int).to_dict(),
        "top_survey_features": survey_importance.head(10).to_dict(orient="records"),
        "top_encoded_response_features": encoded_importance.head(10).to_dict(orient="records"),
        "safety_note": (
            "SHAP values explain model behavior for an EPDS-proxy screening-support prototype. "
            "They are not clinical causes or diagnostic evidence."
        ),
    }
    SHAP_SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_markdown_report(metadata, df, encoded_importance, survey_importance)

    print(f"Saved SHAP encoded importance to {SHAP_GLOBAL_IMPORTANCE_PATH}")
    print(f"Saved SHAP summary to {SHAP_SUMMARY_PATH}")
    print(f"Saved SHAP validation report to {SHAP_VALIDATION_REPORT_PATH}")


if __name__ == "__main__":
    main()
