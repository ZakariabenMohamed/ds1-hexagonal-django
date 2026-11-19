"""Adaptateur de persistance Django ORM : implémente ``LoanRepositoryPort``."""
from __future__ import annotations

from loan_core.domain.models import (
    Applicant,
    Decision,
    DecisionStatus,
    LoanApplication,
    LoanRequest,
)
from loans.models import LoanApplicationRecord


def _to_entity(record: LoanApplicationRecord) -> LoanApplication:
    return LoanApplication(
        id=record.pk,
        applicant=Applicant(record.applicant_name, record.applicant_reference),
        request=LoanRequest(record.amount, record.duration_months, record.monthly_income),
        credit_score=record.credit_score,
        decision=Decision(
            status=DecisionStatus(record.decision_status),
            reasons=tuple(record.decision_reasons),
            monthly_payment=record.monthly_payment,
            debt_ratio=record.debt_ratio,
        ),
        created_at=record.created_at,
    )


class DjangoLoanRepository:
    def save(self, application: LoanApplication) -> LoanApplication:
        values = {
            "applicant_name": application.applicant.name,
            "applicant_reference": application.applicant.reference,
            "amount": application.request.amount,
            "duration_months": application.request.duration_months,
            "monthly_income": application.request.monthly_income,
            "credit_score": application.credit_score,
            "decision_status": application.decision.status.value,
            "decision_reasons": list(application.decision.reasons),
            "monthly_payment": application.decision.monthly_payment,
            "debt_ratio": application.decision.debt_ratio,
            "created_at": application.created_at,
        }
        if application.id is None:
            record = LoanApplicationRecord.objects.create(**values)
        else:
            record, _ = LoanApplicationRecord.objects.update_or_create(
                pk=application.id, defaults=values
            )
        record.refresh_from_db()  # relit les valeurs normalisées par la base
        return _to_entity(record)

    def get(self, application_id: int) -> LoanApplication | None:
        record = LoanApplicationRecord.objects.filter(pk=application_id).first()
        return _to_entity(record) if record else None

    def list_recent(self, limit: int = 50) -> list[LoanApplication]:
        return [_to_entity(r) for r in LoanApplicationRecord.objects.all()[:limit]]
