import pytest

from loan_adapters.scoring import (
    MAX_SCORE,
    MIN_SCORE,
    FixedCreditScore,
    SimulatedCreditBureau,
    UnavailableCreditBureau,
)
from loan_core.application.errors import ScoringUnavailable


def test_simulated_score_is_deterministic():
    bureau = SimulatedCreditBureau()
    assert bureau.score_for("CLI-1001") == bureau.score_for("CLI-1001")


def test_simulated_score_ignores_case_and_surrounding_spaces():
    bureau = SimulatedCreditBureau()
    assert bureau.score_for("CLI-1001") == bureau.score_for("  cli-1001 ")


def test_simulated_scores_stay_in_range_and_vary():
    bureau = SimulatedCreditBureau()
    scores = {bureau.score_for(f"CLI-{n}") for n in range(200)}
    assert all(MIN_SCORE <= s <= MAX_SCORE for s in scores)
    assert len(scores) > 50


def test_fixed_score():
    assert FixedCreditScore(712).score_for("anyone") == 712


def test_unavailable_bureau_raises_the_application_error():
    with pytest.raises(ScoringUnavailable):
        UnavailableCreditBureau().score_for("CLI-1")
