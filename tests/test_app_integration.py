import app as app_module
from app import app, calculate_epds_proxy


def form_data(values):
    return {f"q-{index}": value for index, value in enumerate(values)}


def test_low_risk_application_flow():
    client = app.test_client()
    response = client.post(
        "/test",
        data=form_data(
            ["30-35", "No", "No", "No", "No", "No", "No", "No", "No", "No"]
        ),
    )
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Low postpartum distress risk" in html
    assert "Machine-learning support signal" in html
    assert "Immediate attention recommended" not in html


def test_high_risk_application_flow():
    client = app.test_client()
    response = client.post(
        "/test",
        data=form_data(
            [
                "30-35",
                "Yes",
                "Yes",
                "Two or more days a week",
                "Often",
                "Yes",
                "Yes",
                "Yes",
                "Yes",
                "No",
            ]
        ),
    )
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "High postpartum distress risk" in html
    assert "Responses contributing to the ML support signal" in html


def test_self_harm_application_flow():
    client = app.test_client()
    response = client.post(
        "/test",
        data=form_data(
            ["30-35", "No", "No", "No", "No", "No", "No", "No", "No", "Yes"]
        ),
    )
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Immediate attention recommended" in html
    assert "Machine-learning support signal" in html
    assert "qualified healthcare professional" in html


def test_epds_proxy_scoring_remains_primary_logic():
    features = {
        "Age": "30-35",
        "Feeling sad or Tearful": "No",
        "Irritable towards baby & partner": "No",
        "Trouble sleeping at night": "No",
        "Problems concentrating or making decision": "No",
        "Overeating or loss of appetite": "No",
        "Feeling anxious": "No",
        "Feeling of guilt": "No",
        "Problems of bonding with baby": "No",
        "Suicide attempt": "Yes",
    }
    result = calculate_epds_proxy(features)
    assert result["risk_level"] == "Immediate attention recommended"


def test_missing_field_shows_clear_validation_error():
    client = app.test_client()
    response = client.post(
        "/test",
        data=form_data(["30-35", "No", "No", "No", "No", "No", "No", "No", "No"]),
    )
    html = response.get_data(as_text=True)
    assert response.status_code == 400
    assert "Unable to process the screening responses" in html
    assert "Traceback" not in html


def test_unknown_category_application_flow_does_not_crash():
    client = app.test_client()
    response = client.post(
        "/test",
        data=form_data(
            ["50-55", "No", "No", "No", "No", "No", "No", "No", "No", "No"]
        ),
    )
    assert response.status_code == 200


def test_model_unavailable_shows_graceful_error(monkeypatch):
    monkeypatch.setattr(app_module, "model", None)
    client = app.test_client()
    response = client.post(
        "/test",
        data=form_data(
            ["30-35", "No", "No", "No", "No", "No", "No", "No", "No", "No"]
        ),
    )
    html = response.get_data(as_text=True)
    assert response.status_code == 503
    assert "temporarily unavailable" in html
    assert "FileNotFoundError" not in html


def test_result_ui_avoids_forbidden_clinical_claims():
    client = app.test_client()
    response = client.post(
        "/test",
        data=form_data(
            ["30-35", "Yes", "Yes", "Two or more days a week", "Often", "Yes", "Yes", "Yes", "Yes", "No"]
        ),
    )
    html = response.get_data(as_text=True).lower()
    forbidden = [
        "diagnosed with ppd",
        "guaranteed diagnosis",
        "clinical accuracy",
        "chance of postpartum depression",
    ]
    assert all(phrase not in html for phrase in forbidden)


def test_chat_page_starts_fresh_and_clears_saved_history():
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["chat_history"] = [
            {"role": "user", "content": "I am anxious"},
            {"role": "assistant", "content": "That anxious feeling can be frightening."},
        ]

    response = client.get("/chat")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "I am anxious" not in html
    assert "That anxious feeling can be frightening." not in html
    assert "How are you feeling today?" in html
    with client.session_transaction() as sess:
        assert "chat_history" not in sess


def test_chat_route_applies_urgent_input_guardrail():
    client = app.test_client()
    response = client.post("/chat", json={"message": "I want to harm myself"})
    data = response.get_json()

    assert response.status_code == 200
    assert data["guardrail"] == "urgent_user_language"
    assert "immediate human support" in data["response"]


def test_chat_reset_route_clears_saved_history():
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["chat_history"] = [
            {"role": "user", "content": "old message"},
            {"role": "assistant", "content": "old reply"},
        ]

    response = client.post("/chat/reset")
    data = response.get_json()

    assert response.status_code == 200
    assert data["status"] == "reset"
    with client.session_transaction() as sess:
        assert "chat_history" not in sess


def test_chat_page_has_new_chat_control():
    client = app.test_client()
    response = client.get("/chat")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "resetChat()" in html
    assert "Start a new chat" in html
