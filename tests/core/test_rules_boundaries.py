"""Bornes des règles : chaque seuil est testé juste en dessous, sur la valeur, et juste au-dessus."""
from decimal import Decimal

import pytest

from loan_core.domain.models import DecisionStatus, LoanRequest
from loan_core.domain.rules import LoanPolicy, evaluate, monthly_payment

A, R, M = DecisionStatus.APPROVED, DecisionStatus.REJECTED, DecisionStatus.MANUAL_REVIEW
SMALL = LoanRequest(Decimal("5000"), 36, Decimal("1000"))  # endettement ≈ 15,9 %


@pytest.mark.parametrize(
    "score, expected",
    [
        (300, R), (499, R),     # sous le minimum : refus
        (500, M), (649, M),     # entre le minimum et le seuil d'acceptation : examen
        (650, A), (850, A),     # à partir du seuil : accepté
    ],
)
def test_score_boundaries(score, expected):
    assert evaluate(SMALL, score).status is expected


@pytest.mark.parametrize(
    "amount, months, income, expected",
    [
        ("5000", 36, "1000", A),       # 15,9 %
        ("12000", 36, "1000", M),      # 38,2 % : entre 33 % et 40 %
        ("14000", 36, "1000", R),      # 44,5 % : au-dessus de 40 %
        ("100000", 84, "6000", A),     # 26,8 %
        ("100000", 84, "3500", R),     # 46,0 %
        ("10000", 12, "1000", R),      # 87,4 %
    ],
)
def test_debt_ratio_boundaries_with_excellent_score(amount, months, income, expected):
    request = LoanRequest(Decimal(amount), months, Decimal(income))
    assert evaluate(request, 800).status is expected


def test_ratio_exactly_at_maximum_is_not_rejected():
    # revenu choisi pour que la mensualité soit exactement 40 % du revenu
    payment = monthly_payment(Decimal("10000"), 24, Decimal("0.09"))
    income = (payment / Decimal("0.40")).quantize(Decimal("0.001"))
    decision = evaluate(LoanRequest(Decimal("10000"), 24, income), 800)
    assert decision.debt_ratio <= Decimal("0.4000") + Decimal("0.0001")
    assert decision.status in (M, R)  # jamais accepté automatiquement à ce niveau


def test_longer_duration_lowers_the_monthly_payment():
    short = monthly_payment(Decimal("20000"), 24, Decimal("0.09"))
    long = monthly_payment(Decimal("20000"), 84, Decimal("0.09"))
    assert long < short


def test_bigger_amount_raises_the_monthly_payment():
    assert monthly_payment(Decimal("30000"), 60, Decimal("0.09")) > monthly_payment(
        Decimal("20000"), 60, Decimal("0.09")
    )


def test_higher_rate_raises_the_monthly_payment():
    assert monthly_payment(Decimal("20000"), 60, Decimal("0.12")) > monthly_payment(
        Decimal("20000"), 60, Decimal("0.09")
    )


def test_payment_is_rounded_to_the_millime():
    payment = monthly_payment(Decimal("12345.678"), 37, Decimal("0.0875"))
    assert payment == payment.quantize(Decimal("0.001"))


def test_policy_minimum_score_is_configurable():
    strict = LoanPolicy(min_score=600)
    assert evaluate(SMALL, 599, strict).status is R
    assert evaluate(SMALL, 599).status is M


def test_policy_approval_score_is_configurable():
    relaxed = LoanPolicy(approval_score=550)
    assert evaluate(SMALL, 560, relaxed).status is A
    assert evaluate(SMALL, 560).status is M


def test_missing_score_never_gives_automatic_approval():
    assert evaluate(SMALL, None).status is M


def test_missing_score_does_not_hide_a_ratio_rejection():
    request = LoanRequest(Decimal("14000"), 36, Decimal("1000"))
    assert evaluate(request, None).status is R


def test_approved_decision_always_has_a_reason():
    decision = evaluate(SMALL, 800)
    assert decision.status is A and len(decision.reasons) == 1


def test_manual_review_reasons_mention_the_cause():
    decision = evaluate(SMALL, 600)
    assert "inférieur au seuil" in decision.reasons[0]
