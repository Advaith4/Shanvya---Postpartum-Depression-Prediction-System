import json
from pathlib import Path

import pandas as pd


RAW_DATA_PATH = Path("data/post_data_without_timestamp.csv")
CATBOOST_READY_DATA_PATH = Path("data/ppd_epds_catboost_ready.csv")
REPORT_PATH = Path("data/ppd_epds_preprocessing_report.json")


EXPECTED_COLUMNS = [
    "Age",
    "Feeling sad or Tearful",
    "Irritable towards baby & partner",
    "Trouble sleeping at night",
    "Problems concentrating or making decision",
    "Overeating or loss of appetite",
    "Feeling anxious",
    "Feeling of guilt",
    "Problems of bonding with baby",
    "Suicide attempt",
]


VALUE_NORMALIZATION = {
    "yes": "Yes",
    "no": "No",
    "sometimes": "Sometimes",
    "maybe": "Maybe",
    "often": "Often",
    "not at all": "Not at all",
    "two or more days a week": "Two or more days a week",
    "not interested to say": "Not interested to say",
}


SEVERITY_MAPS = {
    "sad_tearful_score": {
        "No": 0,
        "Sometimes": 2,
        "Yes": 3,
    },
    "irritable_score": {
        "No": 0,
        "Sometimes": 2,
        "Yes": 3,
    },
    "sleep_score": {
        "No": 0,
        "Yes": 2,
        "Two or more days a week": 3,
    },
    "concentration_score": {
        "No": 0,
        "Yes": 2,
        "Often": 3,
    },
    "appetite_score": {
        "No": 0,
        "Not at all": 0,
        "Yes": 3,
    },
    "anxiety_score": {
        "No": 0,
        "Yes": 3,
    },
    "guilt_score": {
        "No": 0,
        "Maybe": 2,
        "Yes": 3,
    },
    "bonding_score": {
        "No": 0,
        "Sometimes": 2,
        "Yes": 3,
    },
    "self_harm_score": {
        "No": 0,
        "Not interested to say": 1,
        "Yes": 3,
    },
}


COLUMN_TO_SCORE = {
    "Feeling sad or Tearful": "sad_tearful_score",
    "Irritable towards baby & partner": "irritable_score",
    "Trouble sleeping at night": "sleep_score",
    "Problems concentrating or making decision": "concentration_score",
    "Overeating or loss of appetite": "appetite_score",
    "Feeling anxious": "anxiety_score",
    "Feeling of guilt": "guilt_score",
    "Problems of bonding with baby": "bonding_score",
    "Suicide attempt": "self_harm_score",
}


EPDS_PROXY_FEATURES = [
    "sad_tearful_score",
    "sleep_score",
    "concentration_score",
    "anxiety_score",
    "guilt_score",
    "bonding_score",
    "irritable_score",
    "self_harm_score",
]


def normalize_value(value):
    if pd.isna(value):
        return value
    normalized = " ".join(str(value).strip().split()).lower()
    return VALUE_NORMALIZATION.get(normalized, str(value).strip())


def age_midpoint(age_band):
    lower, upper = str(age_band).split("-")
    return (int(lower) + int(upper)) / 2


def risk_level(score):
    if score >= 13:
        return "High"
    if score >= 10:
        return "Moderate"
    return "Low"


def main():
    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {RAW_DATA_PATH}")

    raw_df = pd.read_csv(RAW_DATA_PATH)
    missing_columns = [col for col in EXPECTED_COLUMNS if col not in raw_df.columns]
    if missing_columns:
        raise ValueError(f"Missing expected columns: {missing_columns}")

    df = raw_df[EXPECTED_COLUMNS].copy()
    missing_before = df.isna().sum().astype(int).to_dict()
    duplicate_rows_before = int(df.duplicated().sum())

    for column in df.columns:
        df[column] = df[column].map(normalize_value)

    imputation_values = {}
    for column in df.columns:
        if df[column].isna().any():
            mode_value = df[column].mode(dropna=True).iloc[0]
            imputation_values[column] = mode_value
            df[column] = df[column].fillna(mode_value)

    rows_after_imputation = len(df)
    df = df.drop_duplicates().reset_index(drop=True)

    df["age_midpoint"] = df["Age"].map(age_midpoint)

    for source_column, score_column in COLUMN_TO_SCORE.items():
        score_map = SEVERITY_MAPS[score_column]
        df[score_column] = df[source_column].map(score_map)
        if df[score_column].isna().any():
            bad_values = sorted(df.loc[df[score_column].isna(), source_column].dropna().unique())
            raise ValueError(f"Unexpected values in {source_column}: {bad_values}")
        df[score_column] = df[score_column].astype(int)

    # EPDS has 10 items scored 0-3. The source dataset does not contain the
    # exact EPDS questionnaire, so this is a transparent 8-item proxy rescaled
    # to the standard 0-30 EPDS range.
    df["epds_proxy_raw_score_0_24"] = df[EPDS_PROXY_FEATURES].sum(axis=1).astype(int)
    df["epds_proxy_score_0_30"] = (df["epds_proxy_raw_score_0_24"] / 24 * 30).round().astype(int)
    df["epds_proxy_risk_level"] = df["epds_proxy_score_0_30"].map(risk_level)
    df["needs_immediate_attention"] = df["self_harm_score"].eq(3).astype(int)
    df["ppd_risk_label"] = (
        df["epds_proxy_score_0_30"].ge(13) | df["needs_immediate_attention"].eq(1)
    ).astype(int)

    catboost_ready_columns = [
        *EXPECTED_COLUMNS,
        "ppd_risk_label",
    ]
    catboost_ready_df = df[catboost_ready_columns]
    catboost_ready_df.to_csv(CATBOOST_READY_DATA_PATH, index=False)

    report = {
        "source_dataset": str(RAW_DATA_PATH),
        "catboost_ready_dataset": str(CATBOOST_READY_DATA_PATH),
        "rows_before": int(len(raw_df)),
        "rows_after_column_selection": int(rows_after_imputation),
        "rows_after_duplicate_removal": int(len(catboost_ready_df)),
        "duplicate_rows_removed": int(rows_after_imputation - len(catboost_ready_df)),
        "duplicate_rows_before_processing": duplicate_rows_before,
        "missing_values_before_imputation": missing_before,
        "imputation_values": imputation_values,
        "epds_note": (
            "The source data is not the exact Edinburgh Postnatal Depression Scale. "
            "This processed dataset uses an EPDS-style proxy score from available "
            "postpartum distress symptoms and rescales it to 0-30."
        ),
        "epds_proxy_features": EPDS_PROXY_FEATURES,
        "target_definition": {
            "ppd_risk_label": "1 when epds_proxy_score_0_30 >= 13 or self-harm response is Yes; otherwise 0",
            "risk_levels": {
                "Low": "0-9",
                "Moderate": "10-12",
                "High": "13-30",
            },
        },
        "target_distribution": catboost_ready_df["ppd_risk_label"].value_counts().sort_index().astype(int).to_dict(),
        "catboost_categorical_features": EXPECTED_COLUMNS,
        "catboost_target": "ppd_risk_label",
        "excluded_from_catboost_dataset_to_reduce_leakage": [
            "age_midpoint",
            *EPDS_PROXY_FEATURES,
            "epds_proxy_raw_score_0_24",
            "epds_proxy_score_0_30",
            "needs_immediate_attention",
            "epds_proxy_risk_level",
        ],
        "risk_level_distribution": df["epds_proxy_risk_level"].value_counts().to_dict(),
        "score_summary": df[
            ["epds_proxy_raw_score_0_24", "epds_proxy_score_0_30"]
        ].describe().round(2).to_dict(),
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"CatBoost-ready dataset saved to {CATBOOST_READY_DATA_PATH}")
    print(f"Preprocessing report saved to {REPORT_PATH}")
    print(f"Rows: {len(raw_df)} raw -> {len(catboost_ready_df)} processed")


if __name__ == "__main__":
    main()
