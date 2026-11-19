"""Cas d'usage : orchestrent le domaine à travers les ports.

Chaque cas d'usage reçoit ses dépendances (ports) par son constructeur :
c'est l'injection de dépendances « à la main », sans framework.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from loan_core.application.errors import ApplicationNotFound, MemoUnavailable, ScoringUnavailable
from loan_core.application.ports import (
    ClockPort,
    CreditMemoPort,
    LoanRepositoryPort,
    ScoringEnginePort,
)
from loan_core.domain.memo import CreditMemo, render_template_memo, validate_memo
from loan_core.domain.models import Applicant, LoanApplication, LoanRequest
from loan_core.domain.rules import DEFAULT_POLICY, LoanPolicy, evaluate


@dataclass(frozen=True)
class SubmitLoanCommand:
    """Données d'entrée du cas d'usage (indépendantes de HTML ou de JSON)."""

    applicant_name: str
    applicant_reference: str
    amount: Decimal
    duration_months: int
    monthly_income: Decimal


class SubmitLoanApplication:
    """Évalue une nouvelle demande de prêt et l'enregistre."""

    def __init__(
        self,
        repository: LoanRepositoryPort,
        credit_scores: ScoringEnginePort,
        clock: ClockPort,
        policy: LoanPolicy = DEFAULT_POLICY,
    ) -> None:
        self._repository = repository
        self._credit_scores = credit_scores
        self._clock = clock
        self._policy = policy

    def execute(self, command: SubmitLoanCommand) -> LoanApplication:
        # Les objets-valeurs se valident à la construction (InvalidLoanRequest).
        applicant = Applicant(command.applicant_name.strip(), command.applicant_reference.strip())
        request = LoanRequest(command.amount, command.duration_months, command.monthly_income)

        try:
            score: int | None = self._credit_scores.score_for(applicant.reference)
        except ScoringUnavailable:
            score = None  # dégradation maîtrisée : jamais d'acceptation automatique

        decision = evaluate(request, score, self._policy)
        application = LoanApplication(
            applicant=applicant,
            request=request,
            credit_score=score,
            decision=decision,
            created_at=self._clock.now(),
        )
        return self._repository.save(application)


class GetLoanApplication:
    def __init__(self, repository: LoanRepositoryPort) -> None:
        self._repository = repository

    def execute(self, application_id: int) -> LoanApplication:
        application = self._repository.get(application_id)
        if application is None:
            raise ApplicationNotFound(f"Demande {application_id} introuvable.")
        return application


class ListLoanApplications:
    def __init__(self, repository: LoanRepositoryPort) -> None:
        self._repository = repository

    def execute(self, limit: int = 50) -> list[LoanApplication]:
        return self._repository.list_recent(limit)


class GenerateCreditMemo:
    """Demande un mémo à l'assistant, puis le VALIDE avec des règles déterministes.

    Si l'assistant est indisponible ou se trompe (statut contradictoire, chiffres
    différents), on retombe sur le mémo de référence calculé par le domaine.
    """

    def __init__(self, memo_writer: CreditMemoPort) -> None:
        self._memo_writer = memo_writer

    def execute(self, application: LoanApplication) -> CreditMemo:
        try:
            draft = self._memo_writer.draft_memo(application)
        except MemoUnavailable:
            return CreditMemo(
                render_template_memo(application), True, "fallback",
                ("Assistant indisponible.",),
            )
        issues = validate_memo(draft, application)
        if issues:
            return CreditMemo(render_template_memo(application), True, "fallback", issues)
        return CreditMemo(draft, True, "assistant", ())
