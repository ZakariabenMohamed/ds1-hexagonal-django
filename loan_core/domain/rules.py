"""Règles métier d'évaluation d'une demande de prêt (fonctions pures).

Toutes les décisions de la banque se trouvent ici, et nulle part ailleurs.
Les seuils sont regroupés dans ``LoanPolicy`` pour pouvoir les modifier
(et les tester) sans toucher à la logique.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from loan_core.domain.models import Decision, DecisionStatus, LoanRequest

_MILLIME = Decimal("0.001")  # le dinar tunisien a trois décimales
_RATIO_PRECISION = Decimal("0.0001")


@dataclass(frozen=True)
class LoanPolicy:
    annual_rate: Decimal = Decimal("0.09")       # taux annuel fixe (exemple)
    max_debt_ratio: Decimal = Decimal("0.40")    # au-delà : refus
    review_debt_ratio: Decimal = Decimal("0.33")  # entre les deux : examen manuel
    min_score: int = 500                         # en dessous : refus
    approval_score: int = 650                    # en dessous : examen manuel


DEFAULT_POLICY = LoanPolicy()


def monthly_payment(amount: Decimal, duration_months: int, annual_rate: Decimal) -> Decimal:
    """Mensualité d'un prêt à annuités constantes."""
    monthly_rate = annual_rate / 12
    if monthly_rate == 0:
        payment = amount / duration_months
    else:
        payment = amount * monthly_rate / (1 - (1 + monthly_rate) ** -duration_months)
    return payment.quantize(_MILLIME, rounding=ROUND_HALF_UP)


def evaluate(
    request: LoanRequest,
    credit_score: int | None,
    policy: LoanPolicy = DEFAULT_POLICY,
) -> Decision:
    """Décide : accepté, refusé ou à examiner, avec les raisons.

    ``credit_score`` vaut ``None`` quand le service de scoring est indisponible :
    la demande ne peut alors pas être acceptée automatiquement.
    """
    payment = monthly_payment(request.amount, request.duration_months, policy.annual_rate)
    ratio = (payment / request.monthly_income).quantize(_RATIO_PRECISION, rounding=ROUND_HALF_UP)
    ratio_text = f"{ratio * 100:.1f} %"

    rejections: list[str] = []
    if ratio > policy.max_debt_ratio:
        rejections.append(
            f"Mensualité de {payment} TND soit {ratio_text} du revenu "
            f"(maximum {policy.max_debt_ratio * 100:.0f} %)."
        )
    if credit_score is not None and credit_score < policy.min_score:
        rejections.append(f"Score de crédit {credit_score} inférieur au minimum {policy.min_score}.")
    if rejections:
        return Decision(DecisionStatus.REJECTED, tuple(rejections), payment, ratio)

    reviews: list[str] = []
    if credit_score is None:
        reviews.append("Score de crédit indisponible : vérification manuelle requise.")
    elif credit_score < policy.approval_score:
        reviews.append(
            f"Score de crédit {credit_score} inférieur au seuil d'acceptation automatique "
            f"({policy.approval_score})."
        )
    if ratio > policy.review_debt_ratio:
        reviews.append(
            f"Taux d'endettement de {ratio_text} supérieur à {policy.review_debt_ratio * 100:.0f} %."
        )
    if reviews:
        return Decision(DecisionStatus.MANUAL_REVIEW, tuple(reviews), payment, ratio)

    return Decision(
        DecisionStatus.APPROVED,
        (f"Toutes les règles sont satisfaites (endettement {ratio_text}).",),
        payment,
        ratio,
    )
