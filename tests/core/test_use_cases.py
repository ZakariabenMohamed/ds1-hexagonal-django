"""Cas d'usage testés avec des adaptateurs en mémoire : aucune base de données."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from loan_adapters.clock import FixedClock
from loan_adapters.memory import InMemoryLoanRepository
from loan_adapters.scoring import FixedCreditScore, UnavailableCreditBureau
from loan_core.application.errors import ApplicationNotFound
from loan_core.application.use_cases import (
    GetLoanApplication,
    ListLoanApplications,
    SubmitLoanApplication,
    SubmitLoanCommand,
)
from loan_core.domain.errors import InvalidLoanRequest
from loan_core.domain.models import DecisionStatus

NOW = datetime(2026, 11, 12, 9, 0, tzinfo=timezone.utc)


def command(**overrides) -> SubmitLoanCommand:
    values = dict(
        applicant_name="Amine Trabelsi",
        applicant_reference="CLI-1001",
        amount=Decimal("20000"),
        duration_months=60,
        monthly_income=Decimal("2000"),
    )
    values.update(overrides)
    return SubmitLoanCommand(**values)


class SpyScore:
    def __init__(self):
        self.calls = 0

    def score_for(self, applicant_reference: str) -> int:
        self.calls += 1
        return 700


class TickingClock:
    """Avance d'une minute à chaque appel : permet de tester l'ordre."""

    def __init__(self):
        self._instant = NOW

    def now(self) -> datetime:
        self._instant += timedelta(minutes=1)
        return self._instant


def test_approved_application_is_saved_with_id_and_clock_time():
    repository = InMemoryLoanRepository()
    use_case = SubmitLoanApplication(repository, FixedCreditScore(700), FixedClock(NOW))

    application = use_case.execute(command())

    assert application.id == 1
    assert application.decision.status is DecisionStatus.APPROVED
    assert application.credit_score == 700
    assert application.created_at == NOW
    assert repository.get(1) == application


def test_scoring_outage_degrades_to_manual_review():
    use_case = SubmitLoanApplication(InMemoryLoanRepository(), UnavailableCreditBureau(), FixedClock(NOW))

    application = use_case.execute(command())

    assert application.credit_score is None
    assert application.decision.status is DecisionStatus.MANUAL_REVIEW


def test_invalid_request_saves_nothing_and_never_calls_scoring():
    repository, score = InMemoryLoanRepository(), SpyScore()
    use_case = SubmitLoanApplication(repository, score, FixedClock(NOW))

    with pytest.raises(InvalidLoanRequest):
        use_case.execute(command(duration_months=3))

    assert repository.list_recent() == []
    assert score.calls == 0


def test_applicant_fields_are_trimmed():
    use_case = SubmitLoanApplication(InMemoryLoanRepository(), FixedCreditScore(700), FixedClock(NOW))
    application = use_case.execute(command(applicant_name="  Amine  ", applicant_reference=" CLI-1 "))
    assert application.applicant.name == "Amine"
    assert application.applicant.reference == "CLI-1"


def test_get_unknown_application_raises():
    with pytest.raises(ApplicationNotFound):
        GetLoanApplication(InMemoryLoanRepository()).execute(42)


def test_list_returns_newest_first_and_respects_limit():
    repository = InMemoryLoanRepository()
    submit = SubmitLoanApplication(repository, FixedCreditScore(700), TickingClock())
    first = submit.execute(command(applicant_name="Premier"))
    second = submit.execute(command(applicant_name="Deuxième"))
    third = submit.execute(command(applicant_name="Troisième"))

    listing = ListLoanApplications(repository)

    assert [a.id for a in listing.execute()] == [third.id, second.id, first.id]
    assert [a.id for a in listing.execute(limit=2)] == [third.id, second.id]
