"""Entités et objets-valeurs du domaine « demande de crédit ».

Ce module est du Python pur : pas de Django, pas de base de données.
Les objets-valeurs sont immuables (``frozen=True``) et se valident eux-mêmes,
de sorte qu'un objet existant est toujours valide.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum

from loan_core.domain.errors import InvalidLoanRequest

MIN_DURATION_MONTHS = 6
MAX_DURATION_MONTHS = 84
MAX_AMOUNT = Decimal("500000")


class DecisionStatus(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    MANUAL_REVIEW = "MANUAL_REVIEW"


@dataclass(frozen=True)
class Applicant:
    """Le demandeur. ``reference`` est un identifiant client fictif."""

    name: str
    reference: str

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise InvalidLoanRequest("Le nom du demandeur est obligatoire.")
        if not self.reference or not self.reference.strip():
            raise InvalidLoanRequest("La référence client est obligatoire.")


@dataclass(frozen=True)
class LoanRequest:
    """Ce que le client demande : montant, durée et revenu mensuel (en TND)."""

    amount: Decimal
    duration_months: int
    monthly_income: Decimal

    def __post_init__(self) -> None:
        if self.amount <= 0:
            raise InvalidLoanRequest("Le montant doit être strictement positif.")
        if self.amount > MAX_AMOUNT:
            raise InvalidLoanRequest(f"Le montant maximal est de {MAX_AMOUNT} TND.")
        if not MIN_DURATION_MONTHS <= self.duration_months <= MAX_DURATION_MONTHS:
            raise InvalidLoanRequest(
                f"La durée doit être comprise entre {MIN_DURATION_MONTHS} "
                f"et {MAX_DURATION_MONTHS} mois."
            )
        if self.monthly_income <= 0:
            raise InvalidLoanRequest("Le revenu mensuel doit être strictement positif.")


@dataclass(frozen=True)
class Decision:
    """Résultat de l'évaluation : statut, raisons et chiffres qui l'expliquent."""

    status: DecisionStatus
    reasons: tuple[str, ...]
    monthly_payment: Decimal
    debt_ratio: Decimal


@dataclass(frozen=True)
class LoanApplication:
    """Entité principale. ``id`` vaut ``None`` tant qu'elle n'est pas enregistrée."""

    applicant: Applicant
    request: LoanRequest
    credit_score: int | None
    decision: Decision
    created_at: datetime
    id: int | None = None
