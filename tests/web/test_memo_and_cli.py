"""Mémo de crédit affiché par l'interface et l'API ; adaptateur CLI."""
import json
from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
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


def create_application(client, settings, score="fixed:700"):
    settings.LOANS_CREDIT_SCORE_PROVIDER = score
    response = client.post(reverse("loans:apply"), VALID)
    return LoanApplicationRecord.objects.get(), response


def test_detail_page_shows_the_assistant_memo(client, settings):
    record, _ = create_application(client, settings)
    page = client.get(reverse("loans:detail", args=[record.pk])).content.decode()
    assert "Mémo de crédit" in page
    assert "validé par les règles déterministes" in page


def test_faulty_assistant_is_discarded_in_the_page(client, settings):
    record, _ = create_application(client, settings)
    settings.LOANS_MEMO_PROVIDER = "faulty"
    page = client.get(reverse("loans:detail", args=[record.pk])).content.decode()
    assert "le brouillon de l&#x27;assistant a été écarté" in page or "le brouillon de l'assistant a été écarté" in page
    assert "99.999" not in page


def test_api_detail_exposes_the_memo_source(client, settings):
    record, _ = create_application(client, settings)
    body = client.get(reverse("loans:api-application", args=[record.pk])).json()
    assert body["memo"]["source"] == "assistant"

    settings.LOANS_MEMO_PROVIDER = "unavailable"
    body = client.get(reverse("loans:api-application", args=[record.pk])).json()
    assert body["memo"]["source"] == "fallback"
    assert body["memo"]["issues"] == ["Assistant indisponible."]


def test_unknown_memo_provider_is_a_configuration_error(client, settings):
    record, _ = create_application(client, settings)
    settings.LOANS_MEMO_PROVIDER = "nope"
    with pytest.raises(ValueError):
        client.get(reverse("loans:detail", args=[record.pk]))


def test_cli_adapter_evaluates_and_saves(settings):
    settings.LOANS_CREDIT_SCORE_PROVIDER = "fixed:700"
    out = StringIO()

    call_command(
        "evaluate_loan", "--name", "Amine", "--reference", "CLI-1", "--amount", "20000",
        "--months", "60", "--income", "2000", stdout=out,
    )

    record = LoanApplicationRecord.objects.get()
    assert record.decision_status == "APPROVED"
    assert record.monthly_payment == Decimal("415.167")
    assert "APPROVED" in out.getvalue()


def test_cli_adapter_reports_domain_errors():
    with pytest.raises(CommandError, match="durée"):
        call_command(
            "evaluate_loan", "--name", "Amine", "--reference", "CLI-1", "--amount", "20000",
            "--months", "3", "--income", "2000",
        )
    assert LoanApplicationRecord.objects.count() == 0


def test_cli_adapter_rejects_non_numeric_amount():
    with pytest.raises(CommandError):
        call_command(
            "evaluate_loan", "--name", "A", "--reference", "C", "--amount", "abc",
            "--months", "12", "--income", "1000",
        )


def test_api_payload_still_round_trips_with_memo_endpoint(client, settings):
    settings.LOANS_CREDIT_SCORE_PROVIDER = "fixed:700"
    created = client.post(
        reverse("loans:api-applications"),
        data=json.dumps({**VALID, "amount": 20000, "duration_months": 60}),
        content_type="application/json",
    ).json()
    detail = client.get(reverse("loans:api-application", args=[created["id"]])).json()
    assert detail["decision"]["status"] == "APPROVED"
    assert "memo" in detail
