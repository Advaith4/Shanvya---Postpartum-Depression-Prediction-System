# ML Model

## Model

The active secondary ML support model is Logistic Regression.

The saved artifact is a complete sklearn Pipeline:

```text
ColumnTransformer
  -> OneHotEncoder(handle_unknown="ignore")
  -> LogisticRegression(class_weight="balanced")
```

Artifact:

```text
models/ppd_logistic_regression.joblib
```

Metadata:

```text
models/ppd_logistic_regression_metadata.json
```

## Why

Logistic Regression outperformed CatBoost on the project's EPDS-proxy label reconstruction task while being simpler and more interpretable.

Validated nested-threshold results:

```text
F1: 0.9709 +/- 0.0004
ROC-AUC: 0.9928 +/- 0.0076
MCC: 0.8632 +/- 0.0105
```

## Features

The model uses only the approved categorical survey features:

```text
Age
Feeling sad or Tearful
Irritable towards baby & partner
Trouble sleeping at night
Problems concentrating or making decision
Overeating or loss of appetite
Feeling anxious
Feeling of guilt
Problems of bonding with baby
Suicide attempt
```

The model does not use EPDS score columns, risk-level columns, severity score columns, `needs_immediate_attention`, or `age_midpoint`.

## Threshold

The production threshold is:

```text
0.35
```

This is based on the mean of leakage-safe nested CV thresholds:

```text
0.43, 0.33, 0.29, 0.38, 0.33
```

The threshold was not selected on the holdout test set.

## Important Limitation

The target is derived from EPDS-style survey responses. Therefore:

> High model performance demonstrates consistency with the project's proxy-label rule rather than clinical diagnostic validity.

The application must continue to describe the system as an EPDS-proxy postpartum distress screening-support prototype, not a clinically validated postpartum depression diagnostic model.

## Application Role

The deterministic EPDS-proxy scoring system remains the primary screening logic. Logistic Regression is used only as a secondary ML support signal.

The application result is structured as:

```text
Survey responses
  -> EPDS-proxy score/risk
  -> Logistic Regression support signal
  -> Screening-support result
```

The model probability is not a clinical probability and should not be displayed as a chance of postpartum depression.

## Explanation

The app explains the ML support signal using Logistic Regression coefficients. For each user response, the active one-hot encoded category is matched to its learned coefficient. The app displays the top contributing responses in plain language.

These explanations describe model behavior only. They should not be interpreted as medical causes.

## SHAP Explainability

SHAP is integrated as an offline model-audit layer through:

```text
generate_shap_report.py
```

It loads the saved Logistic Regression pipeline, applies the pipeline's existing one-hot encoder, and uses SHAP `LinearExplainer` on the trained classifier. The generated reports are:

```text
reports/shap_global_importance.csv
reports/shap_summary.json
reports/shap_validation_report.md
```

The Flask result UI displays both:

```text
local SHAP explanation values for the user's submitted responses
```

The local SHAP explainer is cached in process after first use so repeated screening submissions do not rebuild the explainer every time.

Global SHAP importance remains available in the generated reports for audit and documentation, but it is not shown in the user-facing Flask result page. The UI keeps only the information a user needs: screening result, ML support score, confidence score, and a short explanation of which submitted responses influenced the model.

For elevated support signals, the UI shows only responses that raised the support signal. For lower support signals, it shows only responses that lowered the signal. This avoids confusing users with protective answers in an elevated-risk result.

In the SHAP report, mean absolute SHAP is used for feature importance. Direction labels for encoded responses come from the trained Logistic Regression coefficients because one-hot SHAP values are baseline-centered and their dataset mean can be misleading as a direction summary.

## Safety Handling

If the self-harm/suicide-related response is positive, the deterministic safety rule takes precedence over the ML model. The app displays an immediate-attention message and recommends prompt professional or emergency support in the user's area.
