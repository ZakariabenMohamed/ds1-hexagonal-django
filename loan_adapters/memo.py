"""Adaptateurs du port ``CreditMemoPort`` (passerelle « assistant IA »).

AUCUN vrai modèle de langage n'est appelé dans ce prototype :
- ``RuleBasedMemoWriter`` rédige un mémo à partir d'un modèle de phrase ;
- ``FaultyMemoWriter`` SIMULE un assistant qui se trompe, pour démontrer que la
  validation déterministe du domaine l'écarte ;
- ``UnavailableMemoWriter`` simule une panne.
Un vrai LLM se brancherait derrière le même port, sans toucher au cœur.
"""
from __future__ import annotations

from loan_core.application.errors import MemoUnavailable
from loan_core.domain.memo import STATUS_LABELS, ratio_percent_text
from loan_core.domain.models import DecisionStatus, LoanApplication


class RuleBasedMemoWriter:
    def draft_memo(self, application: LoanApplication) -> str:
        decision = application.decision
        return (
            f"Synthèse du dossier de {application.applicant.name} : décision {STATUS_LABELS[decision.status]}. "
            f"La mensualité s'élève à {decision.monthly_payment} TND, "
            f"soit {ratio_percent_text(application)} % du revenu mensuel. "
            f"Principal motif : {decision.reasons[0]}"
        )


class FaultyMemoWriter:
    """Simule un assistant qui « hallucine » : statut opposé et mensualité inventée."""

    def draft_memo(self, application: LoanApplication) -> str:
        wrong = (
            STATUS_LABELS[DecisionStatus.REJECTED]
            if application.decision.status is DecisionStatus.APPROVED
            else STATUS_LABELS[DecisionStatus.APPROVED]
        )
        return f"Dossier {wrong}. Mensualité estimée à 99.999 TND, endettement négligeable."


class UnavailableMemoWriter:
    def draft_memo(self, application: LoanApplication) -> str:
        raise MemoUnavailable("Assistant de rédaction indisponible (panne simulée).")
