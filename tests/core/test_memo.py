"""Mémo de crédit : l'assistant propose, les règles déterministes disposent."""
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from loan_adapters.memo import FaultyMemoWriter, RuleBasedMemoWriter, UnavailableMemoWriter
from loan_core.application.use_cases import GenerateCreditMemo
from loan_core.domain.memo import STATUS_LABELS, render_template_memo, validate_memo
from loan_core.domain.models import Applicant, DecisionStatus, LoanApplication, LoanRequest
from loan_core.domain.rules import evaluate

NOW = datetime(2026, 11, 12, 9, 0, tzinfo=timezone.utc)

# (montant, durée, revenu, score) -> statut attendu
SCENARIOS = {
    DecisionStatus.APPROVED: ("20000", 60, "2000", 700),
    DecisionStatus.MANUAL_REVIEW: ("20000", 60, "2000", 600),
    DecisionStatus.REJECTED: ("20000", 60, "2000", 450),
}


def make_application(status: DecisionStatus) -> LoanApplication:
    amount, months, income, score = SCENARIOS[status]
    loan = LoanRequest(Decimal(amount), months, Decimal(income))
    decision = evaluate(loan, score)
    assert decision.status is status  # garde-fou : le scénario produit bien le statut voulu
    return LoanApplication(Applicant("Amine", "CLI-1"), loan, score, decision, NOW, id=7)


@pytest.fixture(params=list(DecisionStatus), ids=lambda s: s.value)
def application(request):
    return make_application(request.param)


def test_reference_memo_always_passes_validation(application):
    assert validate_memo(render_template_memo(application), application) == ()


def test_reference_memo_contains_the_decision_figures(application):
    memo = render_template_memo(application)
    assert str(application.decision.monthly_payment) in memo
    assert STATUS_LABELS[application.decision.status] in memo


def test_rule_based_writer_passes_validation(application):
    draft = RuleBasedMemoWriter().draft_memo(application)
    assert validate_memo(draft, application) == ()


def test_faulty_writer_is_caught_by_validation(application):
    draft = FaultyMemoWriter().draft_memo(application)
    issues = validate_memo(draft, application)
    assert issues, "un mémo erroné doit être détecté"


def test_empty_memo_is_invalid(application):
    assert validate_memo("   ", application) == ("Mémo vide.",)


def test_memo_without_status_is_invalid():
    application = make_application(DecisionStatus.APPROVED)
    memo = f"Mensualité {application.decision.monthly_payment} TND, endettement 20.8 %."
    assert any("statut" in issue for issue in validate_memo(memo, application))


def test_memo_with_wrong_payment_is_invalid():
    application = make_application(DecisionStatus.APPROVED)
    memo = "Dossier accepté. Mensualité 1.000 TND, endettement 20.8 %."
    assert any("mensualité" in issue.lower() for issue in validate_memo(memo, application))


def test_memo_with_wrong_ratio_is_invalid():
    application = make_application(DecisionStatus.APPROVED)
    memo = f"Dossier accepté. Mensualité {application.decision.monthly_payment} TND, endettement 3.0 %."
    assert any("endettement" in issue for issue in validate_memo(memo, application))


def test_memo_contradicting_the_decision_is_invalid():
    application = make_application(DecisionStatus.REJECTED)
    memo = (
        f"Dossier refusé mais finalement accepté. Mensualité {application.decision.monthly_payment} TND, "
        f"endettement {application.decision.debt_ratio * 100:.1f} %."
    )
    assert any("contredit" in issue for issue in validate_memo(memo, application))


def test_use_case_keeps_a_valid_assistant_draft(application):
    memo = GenerateCreditMemo(RuleBasedMemoWriter()).execute(application)
    assert memo.source == "assistant" and memo.issues == ()
    assert memo.text == RuleBasedMemoWriter().draft_memo(application)


def test_use_case_discards_a_faulty_draft_and_falls_back(application):
    memo = GenerateCreditMemo(FaultyMemoWriter()).execute(application)
    assert memo.source == "fallback"
    assert memo.issues
    assert memo.text == render_template_memo(application)
    assert validate_memo(memo.text, application) == ()


def test_use_case_falls_back_when_assistant_is_unavailable(application):
    memo = GenerateCreditMemo(UnavailableMemoWriter()).execute(application)
    assert memo.source == "fallback"
    assert memo.issues == ("Assistant indisponible.",)


def test_final_memo_is_never_inconsistent_whatever_the_assistant(application):
    for writer in (RuleBasedMemoWriter(), FaultyMemoWriter(), UnavailableMemoWriter()):
        memo = GenerateCreditMemo(writer).execute(application)
        assert validate_memo(memo.text, application) == ()
