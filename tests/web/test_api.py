import json

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db

PAYLOAD = {
    "applicant_name": "Salma Ben Ali",
    "applicant_reference": "CLI-1002",
    "amount": 20000,
    "duration_months": 60,
    "monthly_income": "2000",
}


def post(client, payload):
    return client.post(reverse("loans:api-applications"), data=json.dumps(payload), content_type="application/json")


def test_post_creates_an_application(client, settings):
    settings.LOANS_CREDIT_SCORE_PROVIDER = "fixed:700"

    response = post(client, PAYLOAD)

    body = response.json()
    assert response.status_code == 201
    assert body["decision"]["status"] == "APPROVED"
    assert body["decision"]["monthly_payment"] == "415.167"
    assert body["credit_score"] == 700


def test_get_detail_and_list(client, settings):
    settings.LOANS_CREDIT_SCORE_PROVIDER = "fixed:700"
    created = post(client, PAYLOAD).json()

    detail = client.get(reverse("loans:api-application", args=[created["id"]]))
    listing = client.get(reverse("loans:api-applications"))

    assert detail.status_code == 200 and detail.json()["id"] == created["id"]
    assert [r["id"] for r in listing.json()["results"]] == [created["id"]]


def test_domain_error_becomes_400(client):
    response = post(client, {**PAYLOAD, "amount": -10})
    assert response.status_code == 400
    assert "montant" in response.json()["error"].lower()


def test_missing_field_becomes_400(client):
    payload = {k: v for k, v in PAYLOAD.items() if k != "monthly_income"}
    response = post(client, payload)
    assert response.status_code == 400
    assert "monthly_income" in response.json()["error"]


def test_non_numeric_value_becomes_400(client):
    assert post(client, {**PAYLOAD, "amount": "abc"}).status_code == 400


def test_invalid_json_becomes_400(client):
    response = client.post(reverse("loans:api-applications"), data="{pas du json", content_type="application/json")
    assert response.status_code == 400


def test_unknown_application_is_404(client):
    assert client.get(reverse("loans:api-application", args=[12345])).status_code == 404


def test_unsupported_method_is_405(client):
    assert client.delete(reverse("loans:api-applications")).status_code == 405
