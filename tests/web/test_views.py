import pytest
from django.urls import reverse

from loans.models import LoanApplicationRecord

pytestmark = pytest.mark.django_db

VALID = {
    "applicant_name": "Amine Trabelsi",
    "applicant_reference": "CLI-1001",
    "amount": "20000",
    "duration_months": "60",
    "monthly_income": "2000",
}


def test_form_page_loads(client):
    response = client.get(reverse("loans:apply"))
    assert response.status_code == 200
    assert "Nouvelle demande de prêt" in response.content.decode()


def test_valid_submission_redirects_to_an_approved_detail_page(client, settings):
    settings.LOANS_CREDIT_SCORE_PROVIDER = "fixed:700"

    response = client.post(reverse("loans:apply"), VALID)

    record = LoanApplicationRecord.objects.get()
    assert response.status_code == 302
    assert response.url == reverse("loans:detail", args=[record.pk])
    page = client.get(response.url).content.decode()
    assert "Accepté" in page
    assert "20.8 %" in page or "20,8 %" in page


def test_low_score_is_shown_as_rejected(client, settings):
    settings.LOANS_CREDIT_SCORE_PROVIDER = "fixed:400"
    client.post(reverse("loans:apply"), VALID)
    record = LoanApplicationRecord.objects.get()
    assert record.decision_status == "REJECTED"


def test_scoring_outage_leads_to_manual_review(client, settings):
    settings.LOANS_CREDIT_SCORE_PROVIDER = "unavailable"
    response = client.post(reverse("loans:apply"), VALID)
    page = client.get(response.url).content.decode()
    assert "À examiner" in page
    assert "indisponible" in page


def test_domain_validation_error_is_shown_in_the_form(client):
    response = client.post(reverse("loans:apply"), {**VALID, "duration_months": "3"})
    assert response.status_code == 200
    assert "La durée doit être comprise entre" in response.content.decode()
    assert LoanApplicationRecord.objects.count() == 0


def test_missing_field_is_reported_by_the_form(client):
    response = client.post(reverse("loans:apply"), {**VALID, "amount": ""})
    assert response.status_code == 200
    assert LoanApplicationRecord.objects.count() == 0


def test_unknown_application_returns_404(client):
    assert client.get(reverse("loans:detail", args=[999])).status_code == 404


def test_history_page_lists_applications(client, settings):
    settings.LOANS_CREDIT_SCORE_PROVIDER = "fixed:700"
    client.post(reverse("loans:apply"), VALID)
    page = client.get(reverse("loans:list")).content.decode()
    assert "Amine Trabelsi" in page
