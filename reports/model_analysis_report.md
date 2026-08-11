# Model Analysis Report

## Project

This project is a Flask-based postpartum distress screening-support prototype. It uses an EPDS-style proxy screening dataset and a Logistic Regression model as a secondary machine-learning support signal.

## Dataset Details

| Item | Value |
|---|---:|
| Source dataset | `data/post_data_without_timestamp.csv` |
| Final model dataset | `data/ppd_epds_catboost_ready.csv` |
| Original rows | 1503 |
| Rows after duplicate removal | 326 |
| Duplicate rows removed | 1177 |
| Target column | `ppd_risk_label` |
| Non-elevated-risk records | 67 |
| Elevated-risk records | 259 |

## Target Definition

The target label `ppd_risk_label` is derived from the EPDS-style proxy score:

| Label | Meaning |
|---|---|
| `0` | Lower proxy-risk pattern |
| `1` | Elevated proxy-risk pattern |

Label `1` is assigned when the EPDS-proxy score is at least 13 or when the self-harm related response is positive.

## Risk Level Distribution

| Risk level | Count |
|---|---:|
| Low | 18 |
| Moderate | 61 |
| High | 247 |

## EPDS-Proxy Score Statistics

| Metric | Raw score 0-24 | Rescaled score 0-30 |
|---|---:|---:|
| Count | 326 | 326 |
| Mean | 12.83 | 16.03 |
| Standard deviation | 3.37 | 4.23 |
| Minimum | 3 | 4 |
| 25th percentile | 11 | 14 |
| Median | 13 | 16 |
| 75th percentile | 15 | 19 |
| Maximum | 22 | 28 |

## Model Details

| Item | Value |
|---|---|
| Active model | Logistic Regression |
| Model version | 1.0.0 |
| Model artifact | `models/ppd_logistic_regression.joblib` |
| Metadata file | `models/ppd_logistic_regression_metadata.json` |
| Preprocessing | Scikit-learn Pipeline with ColumnTransformer and OneHotEncoder |
| Class imbalance handling | `class_weight="balanced"` |
| Production threshold | 0.35 |
| Validation method | 5-fold Stratified Cross-Validation with nested threshold selection |

## Model Features

The model uses the following input features:

| Feature |
|---|
| Age |
| Feeling sad or Tearful |
| Irritable towards baby & partner |
| Trouble sleeping at night |
| Problems concentrating or making decision |
| Overeating or loss of appetite |
| Feeling anxious |
| Feeling of guilt |
| Problems of bonding with baby |
| Suicide attempt |

## Excluded Leakage-Prone Columns

The following columns were excluded from the model dataset to reduce label leakage:

| Excluded column |
|---|
| `age_midpoint` |
| `sad_tearful_score` |
| `sleep_score` |
| `concentration_score` |
| `anxiety_score` |
| `guilt_score` |
| `bonding_score` |
| `irritable_score` |
| `self_harm_score` |
| `epds_proxy_raw_score_0_24` |
| `epds_proxy_score_0_30` |
| `needs_immediate_attention` |
| `epds_proxy_risk_level` |

## Validation Metrics

| Metric | Mean | Standard deviation |
|---|---:|---:|
| F1 score | 0.9709 | 0.0004 |
| ROC-AUC | 0.9928 | 0.0076 |
| MCC | 0.8632 | 0.0105 |

## Threshold Selection

The production threshold is `0.35`. It is based on the mean of leakage-safe nested cross-validation thresholds: `0.43`, `0.33`, `0.29`, `0.38`, and `0.33`.

## SHAP Explainability

SHAP is used to explain model behavior. The project uses SHAP `LinearExplainer` with the trained Logistic Regression model.

| SHAP item | Value |
|---|---|
| SHAP script | `generate_shap_report.py` |
| SHAP summary | `reports/shap_summary.json` |
| SHAP validation report | `reports/shap_validation_report.md` |
| SHAP global importance | `reports/shap_global_importance.csv` |
| Rows explained | 326 |

## Top SHAP Survey Features

| Rank | Feature | Mean absolute SHAP |
|---:|---|---:|
| 1 | Suicide attempt | 2.8168 |
| 2 | Feeling sad or Tearful | 1.7582 |
| 3 | Feeling anxious | 1.5114 |
| 4 | Problems of bonding with baby | 1.4759 |
| 5 | Irritable towards baby & partner | 1.3821 |

## Application Behavior

The deterministic EPDS-proxy score remains the primary screening result. The Logistic Regression model provides a secondary support signal, model probability, confidence score, and local SHAP explanation in the Flask result page.

## Failure Cases and Limitations

| Limitation | Detail |
|---|---|
| Proxy labels | The target is derived from EPDS-style survey responses, not clinician diagnosis. |
| Small dataset | The final model dataset has only 326 rows. |
| Class imbalance | Elevated-risk records are much higher than non-elevated-risk records. |
| No external validation | The model has not been tested on an independent clinical dataset. |
| Not diagnostic | The model supports screening only and must not be used as a medical diagnosis. |

## Deployment

| Item | Value |
|---|---|
| Framework | Flask |
| Local run command | `python app.py` |
| Local URL | `http://localhost:5001` |
| Chat API | Hugging Face API, only when `HF_TOKEN` is configured |

## Final Note

The reported performance shows that the model is highly consistent with the project's EPDS-proxy label rule. It does not prove clinical diagnostic accuracy.
