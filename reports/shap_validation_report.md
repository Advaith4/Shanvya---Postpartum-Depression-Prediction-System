# SHAP Explainability Report

## Scope

This report explains the saved Logistic Regression screening-support model using SHAP.
SHAP is used offline for model audit and documentation. The live Flask app keeps using fast coefficient-based explanations.

## Model

- Model: `logistic_regression`
- Artifact: `models\ppd_logistic_regression.joblib`
- Dataset: `data\ppd_epds_catboost_ready.csv`
- Rows explained: `326`
- Target: `ppd_risk_label`
- Class distribution: `{0: 67, 1: 259}`

## Top Survey Features

| Rank | Feature | Mean absolute SHAP |
| --- | --- | ---: |
| 1 | Suicide attempt | 2.816808 |
| 2 | Feeling sad or Tearful | 1.758197 |
| 3 | Feeling anxious | 1.511447 |
| 4 | Problems of bonding with baby | 1.475855 |
| 5 | Irritable towards baby & partner | 1.382138 |
| 6 | Feeling of guilt | 1.307610 |
| 7 | Problems concentrating or making decision | 1.032771 |
| 8 | Trouble sleeping at night | 0.802208 |
| 9 | Age | 0.463553 |
| 10 | Overeating or loss of appetite | 0.363889 |

## Top Encoded Response Features

| Rank | Survey feature | Response | Mean absolute SHAP | Model coefficient direction |
| --- | --- | --- | ---: | --- |
| 1 | Suicide attempt | Yes | 1.609584 | pushes_toward_elevated_support_signal |
| 2 | Suicide attempt | No | 0.949781 | pushes_toward_lower_support_signal |
| 3 | Feeling anxious | Yes | 0.896019 | pushes_toward_elevated_support_signal |
| 4 | Feeling sad or Tearful | Yes | 0.895291 | pushes_toward_elevated_support_signal |
| 5 | Irritable towards baby & partner | Yes | 0.790653 | pushes_toward_elevated_support_signal |
| 6 | Feeling sad or Tearful | No | 0.727019 | pushes_toward_lower_support_signal |
| 7 | Problems of bonding with baby | No | 0.638967 | pushes_toward_lower_support_signal |
| 8 | Feeling anxious | No | 0.615428 | pushes_toward_lower_support_signal |
| 9 | Irritable towards baby & partner | No | 0.569094 | pushes_toward_lower_support_signal |
| 10 | Feeling of guilt | Yes | 0.559457 | pushes_toward_elevated_support_signal |

Mean absolute SHAP is used for importance. Direction is shown from the trained Logistic Regression coefficient because one-hot SHAP values are baseline-centered and their dataset mean can be misleading as a direction label.

## Interpretation Safety

SHAP values describe how this trained model uses survey responses. They are not medical causes, clinical explanations, or diagnostic evidence.
The model target is an EPDS-style proxy label, so these explanations reflect the proxy labeling rule and the available dataset.
