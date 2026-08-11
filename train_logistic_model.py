import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from ml_inference import METADATA_PATH, MODEL_PATH, MODEL_THRESHOLD
from preprocess_dataset import CATBOOST_READY_DATA_PATH, EXPECTED_COLUMNS, main as preprocess_dataset


TARGET = "ppd_risk_label"
MODEL_VERSION = "1.0.0"


VALIDATION_METRICS = {
    "validation_method": "5-fold Stratified Cross-Validation with nested threshold selection",
    "f1": {"mean": 0.9709, "std": 0.0004},
    "roc_auc": {"mean": 0.9928, "std": 0.0076},
    "mcc": {"mean": 0.8632, "std": 0.0105},
}


def build_pipeline():
    return Pipeline(
        steps=[
            (
                "preprocess",
                ColumnTransformer(
                    transformers=[
                        (
                            "categorical",
                            OneHotEncoder(handle_unknown="ignore"),
                            EXPECTED_COLUMNS,
                        )
                    ]
                ),
            ),
            (
                "model",
                LogisticRegression(
                    class_weight="balanced",
                    max_iter=1000,
                    random_state=42,
                    solver="liblinear",
                ),
            ),
        ]
    )


def main():
    Path("models").mkdir(exist_ok=True)
    if not CATBOOST_READY_DATA_PATH.exists():
        preprocess_dataset()

    df = pd.read_csv(CATBOOST_READY_DATA_PATH)
    missing_columns = [column for column in [*EXPECTED_COLUMNS, TARGET] if column not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing expected columns: {missing_columns}")

    X = df[EXPECTED_COLUMNS]
    y = df[TARGET].astype(int)

    pipeline = build_pipeline()
    pipeline.fit(X, y)
    joblib.dump(pipeline, MODEL_PATH)

    metadata = {
        "model_name": "logistic_regression",
        "model_version": MODEL_VERSION,
        "artifact_path": str(MODEL_PATH),
        "training_dataset": str(CATBOOST_READY_DATA_PATH),
        "training_rows": int(len(df)),
        "features": EXPECTED_COLUMNS,
        "target": TARGET,
        "class_distribution": y.value_counts().sort_index().astype(int).to_dict(),
        "class_balance_strategy": "LogisticRegression(class_weight='balanced')",
        "preprocessing": "sklearn Pipeline with ColumnTransformer and OneHotEncoder(handle_unknown='ignore')",
        "threshold": MODEL_THRESHOLD,
        "threshold_rationale": (
            "Production threshold is 0.35, based on the mean of leakage-safe nested CV "
            "thresholds 0.43, 0.33, 0.29, 0.38, 0.33 rounded to two decimals. "
            "It was not selected on the holdout test set."
        ),
        "validation_method": VALIDATION_METRICS["validation_method"],
        "validation_metrics": VALIDATION_METRICS,
        "known_limitations": [
            "Metrics measure consistency with the project's EPDS-proxy labeling rule, not clinical diagnostic accuracy.",
            "Target is derived from EPDS-style survey responses.",
            "No clinician-confirmed diagnostic labels are available.",
            "No external validation dataset is available.",
            "Dataset contains 326 final rows with class imbalance.",
        ],
        "intended_use": "Secondary ML support signal for an EPDS-proxy postpartum distress screening-support prototype.",
    }
    METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"Saved Logistic Regression pipeline to {MODEL_PATH}")
    print(f"Saved model metadata to {METADATA_PATH}")


if __name__ == "__main__":
    main()
