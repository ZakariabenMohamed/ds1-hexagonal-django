from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from loan_core.domain.errors import InvalidLoanRequest
from loan_core.domain.models import Applicant, LoanRequest


@pytest.mark.parametrize(
    "amount, months, income",
    [
        ("0", 12, "1000"),         # montant nul
        ("-5", 12, "1000"),        # montant négatif
        ("500001", 12, "1000"),    # au-dessus du maximum
        ("1000", 5, "1000"),       # durée trop courte
        ("1000", 85, "1000"),      # durée trop longue
        ("1000", 12, "0"),         # revenu nul
    ],
)
def test_invalid_loan_requests_are_rejected(amount, months, income):
    with pytest.raises(InvalidLoanRequest):
        LoanRequest(Decimal(amount), months, Decimal(income))


def test_boundary_values_are_accepted():
    LoanRequest(Decimal("500000"), 6, Decimal("1"))
    LoanRequest(Decimal("0.001"), 84, Decimal("1"))


@pytest.mark.parametrize("name, reference", [("", "C1"), ("  ", "C1"), ("Ali", ""), ("Ali", "   ")])
def test_applicant_requires_name_and_reference(name, reference):
    with pytest.raises(InvalidLoanRequest):
        Applicant(name, reference)


def test_value_objects_are_immutable():
    request = LoanRequest(Decimal("1000"), 12, Decimal("1000"))
    with pytest.raises(FrozenInstanceError):
        request.amount = Decimal("1")  # type: ignore[misc]
