"""Tests de contrat : les deux adaptateurs doivent se comporter à l'identique.

Les mêmes tests s'exécutent contre l'adaptateur mémoire et l'adaptateur Django
ORM. C'est la preuve qu'ils sont interchangeables derrière ``LoanRepositoryPort``.
"""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from loan_adapters.memory import InMemoryLoanRepository
from loan_core.domain.models import Applicant, LoanApplication, LoanRequest
from loan_core.domain.rules import evaluate
from loans.repository import DjangoLoanRepository

BASE_TIME = datetime(2026, 11, 12, 9, 0, tzinfo=timezone.utc)


@pytest.fixture(params=["memory", pytest.param("django", marks=pytest.mark.django_db)])
def repository(request):
    if request.param == "memory":
        return InMemoryLoanRepository()
    return DjangoLoanRepository()


def make_application(name="Amine", minutes=0, score=700) -> LoanApplication:
    loan = LoanRequest(Decimal("20000"), 60, Decimal("2000"))
    return LoanApplication(
        applicant=Applicant(name, "CLI-1"),
        request=loan,
        credit_score=score,
        decision=evaluate(loan, score),
        created_at=BASE_TIME + timedelta(minutes=minutes),
    )


def test_save_assigns_an_id_and_round_trips(repository):
    saved = repository.save(make_application())

    assert saved.id is not None
    assert repository.get(saved.id) == saved
    assert saved.decision.reasons == make_application().decision.reasons


def test_none_credit_score_round_trips(repository):
    saved = repository.save(make_application(score=None))
    assert repository.get(saved.id).credit_score is None


def test_get_unknown_id_returns_none(repository):
    assert repository.get(9999) is None


def test_saving_with_existing_id_updates_instead_of_duplicating(repository):
    saved = repository.save(make_application(name="Avant"))
    repository.save(replace(saved, applicant=Applicant("Après", "CLI-1")))

    assert len(repository.list_recent()) == 1
    assert repository.get(saved.id).applicant.name == "Après"


def test_list_recent_is_newest_first_and_limited(repository):
    oldest = repository.save(make_application(name="A", minutes=0))
    middle = repository.save(make_application(name="B", minutes=1))
    newest = repository.save(make_application(name="C", minutes=2))

    assert [a.id for a in repository.list_recent()] == [newest.id, middle.id, oldest.id]
    assert [a.id for a in repository.list_recent(limit=1)] == [newest.id]
