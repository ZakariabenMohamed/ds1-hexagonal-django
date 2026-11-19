"""Mémo de crédit : modèle et validation DÉTERMINISTE.

Un assistant (IA ou non) peut rédiger le mémo, mais il n'a jamais le dernier mot :
les chiffres et le statut du mémo sont vérifiés par des règles pures contre la
décision réellement prise par le domaine. Un mémo qui se contredit est écarté.
"""
from __future__ import annotations

from dataclasses import dataclass

from loan_core.domain.models import DecisionStatus, LoanApplication

STATUS_LABELS: dict[DecisionStatus, str] = {
    DecisionStatus.APPROVED: "accepté",
    DecisionStatus.REJECTED: "refusé",
    DecisionStatus.MANUAL_REVIEW: "à examiner",
}


def ratio_percent_text(application: LoanApplication) -> str:
    return f"{application.decision.debt_ratio * 100:.1f}"


@dataclass(frozen=True)
class CreditMemo:
    text: str
    validated: bool          # True si le texte final a passé toutes les règles
    source: str              # "assistant" ou "fallback" (modèle déterministe)
    issues: tuple[str, ...]  # problèmes détectés sur le brouillon de l'assistant


def render_template_memo(application: LoanApplication) -> str:
    """Mémo de référence, produit uniquement à partir de la décision (sans IA)."""
    decision = application.decision
    score = "indisponible" if application.credit_score is None else str(application.credit_score)
    reasons = " ".join(decision.reasons)
    return (
        f"Dossier {application.id or 'nouveau'} — {application.applicant.name}. "
        f"Décision : {STATUS_LABELS[decision.status]}. "
        f"Montant demandé : {application.request.amount} TND sur {application.request.duration_months} mois. "
        f"Mensualité : {decision.monthly_payment} TND, soit {ratio_percent_text(application)} % du revenu. "
        f"Score de crédit : {score}. Motifs : {reasons}"
    )


def validate_memo(text: str, application: LoanApplication) -> tuple[str, ...]:
    """Retourne la liste des problèmes ; vide si le mémo est cohérent avec la décision."""
    issues: list[str] = []
    lowered = text.lower()
    decision = application.decision

    if not text or not text.strip():
        return ("Mémo vide.",)

    expected = STATUS_LABELS[decision.status]
    if expected not in lowered:
        issues.append(f"Le statut « {expected} » n'apparaît pas dans le mémo.")
    for status, label in STATUS_LABELS.items():
        if status is not decision.status and label in lowered:
            issues.append(f"Le mémo mentionne « {label} », qui contredit la décision.")

    if str(decision.monthly_payment) not in text:
        issues.append(f"La mensualité {decision.monthly_payment} TND est absente ou différente.")
    if ratio_percent_text(application) not in text:
        issues.append(f"Le taux d'endettement {ratio_percent_text(application)} % est absent ou différent.")
    return tuple(issues)
