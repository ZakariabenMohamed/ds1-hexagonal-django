"""Ports : les « prises » que le cœur définit et que les adaptateurs implémentent.

Ce sont des interfaces (``typing.Protocol``). Le cœur ne dépend que d'elles,
jamais d'une technologie concrète. C'est l'inversion de dépendance :
c'est le cœur qui impose le contrat, l'infrastructure s'y conforme.
"""
from __future__ import annotations

from datetime import datetime
from typing import Protocol

from loan_core.domain.models import LoanApplication


class LoanRepositoryPort(Protocol):
    """Port de sortie : persistance des demandes."""

    def save(self, application: LoanApplication) -> LoanApplication:
        """Enregistre la demande et la retourne avec son ``id`` renseigné."""
        ...

    def get(self, application_id: int) -> LoanApplication | None:
        ...

    def list_recent(self, limit: int = 50) -> list[LoanApplication]:
        """Demandes les plus récentes en premier."""
        ...


class ScoringEnginePort(Protocol):
    """Port de sortie : score de crédit d'un client (entre 300 et 850)."""

    def score_for(self, applicant_reference: str) -> int:
        """Lève ``ScoringUnavailable`` si le service ne répond pas."""
        ...


class CreditMemoPort(Protocol):
    """Port de sortie : un assistant (IA ou non) qui rédige un mémo de crédit.

    Le texte retourné n'est jamais cru sur parole : le cas d'usage le valide
    avec des règles déterministes du domaine.
    """

    def draft_memo(self, application: LoanApplication) -> str:
        """Lève ``MemoUnavailable`` si l'assistant ne répond pas."""
        ...


class ClockPort(Protocol):
    """Port de sortie : l'heure courante (rend les tests déterministes)."""

    def now(self) -> datetime:
        ...
