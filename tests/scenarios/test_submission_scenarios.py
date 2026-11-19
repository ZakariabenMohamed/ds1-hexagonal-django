"""Même suite de scénarios, deux adaptateurs de persistance : faux dépôt et Django ORM.

Les identifiants ``fake_repo`` et ``orm_repo`` permettent de chronométrer chaque
variante séparément (voir scripts/benchmark.py) :
    pytest tests/scenarios -k fake_repo
    pytest tests/scenarios -k orm_repo
"""
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from loan_adapters.clock import FixedClock
from loan_adapters.memory import InMemoryLoanRepository
from loan_adapters.scoring import FixedCreditScore
from loan_core.application.use_cases import SubmitLoanApplication, SubmitLoanCommand
from loan_core.domain.models import DecisionStatus
from loans.repository import DjangoLoanRepository

A, R, M = DecisionStatus.APPROVED, DecisionStatus.REJECTED, DecisionStatus.MANUAL_REVIEW
NOW = datetime(2026, 11, 12, 9, 0, tzinfo=timezone.utc)

SCENARIOS = [
    # montant, durée, revenu, score, statut attendu
    ("20000", 60, "2000", 700, A),
    ("20000", 60, "2000", 600, M),
    ("20000", 60, "2000", 450, R),
    ("20000", 60, "1200", 800, M),
    ("50000", 24, "1500", 800, R),
    ("5000", 36, "1000", 800, A),
    ("5000", 36, "1000", 650, A),
    ("5000", 36, "1000", 649, M),
    ("5000", 36, "1000", 500, M),
    ("5000", 36, "1000", 499, R),
    ("12000", 36, "1000", 800, M),
    ("14000", 36, "1000", 800, R),
    ("100000", 84, "6000", 750, A),
]


@pytest.fixture(params=["fake_repo", pytest.param("orm_repo", marks=pytest.mark.django_db)])
def repository(request):
    if request.param == "fake_repo":
        return InMemoryLoanRepository()
    return DjangoLoanRepository()


@pytest.mark.parametrize("amount, months, income, score, expected", SCENARIOS)
def test_scenario(repository, amount, months, income, score, expected):
    use_case = SubmitLoanApplication(repository, FixedCreditScore(score), FixedClock(NOW))

    application = use_case.execute(
        SubmitLoanCommand("Client Test", "CLI-T", Decimal(amount), months, Decimal(income))
    )

    assert application.decision.status is expected
    assert repository.get(application.id) == application
    assert [a.id for a in repository.list_recent()] == [application.id]
