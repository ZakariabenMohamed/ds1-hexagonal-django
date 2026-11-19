"""Règles métier : Python pur, aucune base de données (pytest-django la bloquerait)."""
from decimal import Decimal

import pytest

from loan_core.domain.models import DecisionStatus, LoanRequest
from loan_core.domain.rules import LoanPolicy, evaluate, monthly_payment

A, R, M = DecisionStatus.APPROVED, DecisionStatus.REJECTED, DecisionStatus.MANUAL_REVIEW


def test_monthly_payment_annuity_formula():
    assert monthly_payment(Decimal("20000"), 60, Decimal("0.09")) == Decimal("415.167")


def test_monthly_payment_without_interest():
    assert monthly_payment(Decimal("1200"), 12, Decimal("0")) == Decimal("100.000")


@pytest.mark.parametrize(
    "amount, months, income, score, expected",
    [
        ("20000", 60, "2000", 700, A),   # endettement 20,8 %, bon score
        ("20000", 60, "2000", 600, M),   # score entre 500 et 649
        ("20000", 60, "2000", 450, R),   # score trop bas
        ("20000", 60, "2000", None, M),  # scoring indisponible
        ("20000", 60, "1200", 800, M),   # endettement 34,6 % : entre 33 % et 40 %
        ("50000", 24, "1500", 800, R),   # endettement très élevé
    ],
)
def test_decision_matrix(amount, months, income, score, expected):
    request = LoanRequest(Decimal(amount), months, Decimal(income))
    assert evaluate(request, score).status is expected


def test_rejection_lists_every_reason():
    request = LoanRequest(Decimal("20000"), 60, Decimal("1000"))  # endettement 41,5 %
    decision = evaluate(request, 400)
    assert decision.status is R
    assert len(decision.reasons) == 2


def test_decision_exposes_figures_that_explain_it():
    decision = evaluate(LoanRequest(Decimal("20000"), 60, Decimal("2000")), 700)
    assert decision.monthly_payment == Decimal("415.167")
    assert decision.debt_ratio == Decimal("0.2076")


def test_policy_thresholds_are_configurable():
    request = LoanRequest(Decimal("20000"), 60, Decimal("1000"))  # endettement 41,5 %
    assert evaluate(request, 800).status is R
    lenient = LoanPolicy(max_debt_ratio=Decimal("0.50"), review_debt_ratio=Decimal("0.45"))
    assert evaluate(request, 800, lenient).status is A
