import pytest

from ml_inference import (
    ModelInputError,
    load_model_bundle,
    model_support_band,
    predict_support_signal,
)
from preprocess_dataset import EXPECTED_COLUMNS


LOW_RISK_INPUT = {
    "Age": "30-35",
    "Feeling sad or Tearful": "No",
    "Irritable towards baby & partner": "No",
    "Trouble sleeping at night": "No",
    "Problems concentrating or making decision": "No",
    "Overeating or loss of appetite": "No",
    "Feeling anxious": "No",
    "Feeling of guilt": "No",
    "Problems of bonding with baby": "No",
    "Suicide attempt": "No",
}


HIGH_RISK_INPUT = {
    "Age": "30-35",
    "Feeling sad or Tearful": "Yes",
    "Irritable towards baby & partner": "Yes",
    "Trouble sleeping at night": "Two or more days a week",
    "Problems concentrating or making decision": "Often",
    "Overeating or loss of appetite": "Yes",
    "Feeling anxious": "Yes",
    "Feeling of guilt": "Yes",
    "Problems of bonding with baby": "Yes",
    "Suicide attempt": "No",
}


def test_model_artifact_loads():
    model, metadata = load_model_bundle()
    assert model is not None
    assert metadata["model_name"] == "logistic_regression"
    assert metadata["features"] == EXPECTED_COLUMNS


def test_valid_input_produces_prediction():
    signal = predict_support_signal(HIGH_RISK_INPUT)
    assert signal["model_name"] == "logistic_regression"
    assert signal["predicted_label"] in {0, 1}
    assert 0 <= signal["probability"] <= 1
    assert signal["threshold"] == pytest.approx(0.35)
    assert signal["support_signal"] in {"Elevated", "Not elevated"}


def test_unknown_category_does_not_crash_pipeline():
    unknown_input = dict(LOW_RISK_INPUT)
    unknown_input["Age"] = "50-55"
    signal = predict_support_signal(unknown_input)
    assert signal["predicted_label"] in {0, 1}
    assert 0 <= signal["probability"] <= 1


def test_missing_required_feature_raises_clear_error():
    incomplete = dict(LOW_RISK_INPUT)
    incomplete.pop("Age")
    with pytest.raises(ModelInputError, match="Missing required feature"):
        predict_support_signal(incomplete)


def test_documented_imputation_for_missing_categorical_values():
    imputed = dict(HIGH_RISK_INPUT)
    imputed["Feeling of guilt"] = ""
    signal = predict_support_signal(imputed)
    assert signal["predicted_label"] in {0, 1}


def test_threshold_comparison_behavior_with_stub_model():
    class StubModel:
        def predict_proba(self, _input_data):
            return [[0.6, 0.4]]

    metadata = {
        "model_name": "logistic_regression",
        "threshold": 0.35,
    }
    signal = predict_support_signal(LOW_RISK_INPUT, StubModel(), metadata)
    assert signal["probability"] == pytest.approx(0.4)
    assert signal["predicted_label"] == 1

    metadata["threshold"] = 0.45
    signal = predict_support_signal(LOW_RISK_INPUT, StubModel(), metadata)
    assert signal["predicted_label"] == 0


def test_same_input_is_deterministic():
    first = predict_support_signal(HIGH_RISK_INPUT)
    second = predict_support_signal(HIGH_RISK_INPUT)
    assert first == second


def test_regression_fixture_expected_direction():
    low = predict_support_signal(LOW_RISK_INPUT)
    high = predict_support_signal(HIGH_RISK_INPUT)
    assert low["probability"] < high["probability"]
    assert high["predicted_label"] == 1


def test_top_contributing_features_are_returned():
    signal = predict_support_signal(HIGH_RISK_INPUT)
    assert signal["top_contributions"]
    first = signal["top_contributions"][0]
    assert {"feature", "response", "direction", "importance"} <= set(first)
    assert first["direction"] in {"increases_support_signal", "decreases_support_signal"}


def test_support_band_text_is_not_clinical_probability():
    band = model_support_band(0.8, 0.35)
    assert "ML support" in band
    assert "diagnosis" not in band.lower()
