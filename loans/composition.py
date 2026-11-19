"""Composition root : le SEUL endroit où l'on choisit les adaptateurs concrets.

Les vues demandent un cas d'usage ici ; elles ne savent ni quelle base de
données ni quel service de scoring est utilisé. Pour changer d'adaptateur,
on modifie ce fichier (ou un réglage), jamais le cœur.
"""
from __future__ import annotations

from django.conf import settings

from loan_adapters.clock import SystemClock
from loan_adapters.memo import FaultyMemoWriter, RuleBasedMemoWriter, UnavailableMemoWriter
from loan_adapters.scoring import FixedCreditScore, SimulatedCreditBureau, UnavailableCreditBureau
from loan_core.application.ports import CreditMemoPort, ScoringEnginePort
from loan_core.application.use_cases import (
    GenerateCreditMemo,
    GetLoanApplication,
    ListLoanApplications,
    SubmitLoanApplication,
)
from loans.repository import DjangoLoanRepository


def build_credit_scores() -> ScoringEnginePort:
    provider = getattr(settings, "LOANS_CREDIT_SCORE_PROVIDER", "simulated")
    if provider == "simulated":
        return SimulatedCreditBureau()
    if provider == "unavailable":
        return UnavailableCreditBureau()
    if provider.startswith("fixed:"):
        return FixedCreditScore(int(provider.split(":", 1)[1]))
    raise ValueError(f"LOANS_CREDIT_SCORE_PROVIDER inconnu : {provider!r}")


def submit_loan_application() -> SubmitLoanApplication:
    return SubmitLoanApplication(DjangoLoanRepository(), build_credit_scores(), SystemClock())


def get_loan_application() -> GetLoanApplication:
    return GetLoanApplication(DjangoLoanRepository())


def list_loan_applications() -> ListLoanApplications:
    return ListLoanApplications(DjangoLoanRepository())


def build_memo_writer() -> CreditMemoPort:
    provider = getattr(settings, "LOANS_MEMO_PROVIDER", "rule_based")
    writers = {
        "rule_based": RuleBasedMemoWriter,
        "faulty": FaultyMemoWriter,
        "unavailable": UnavailableMemoWriter,
    }
    if provider not in writers:
        raise ValueError(f"LOANS_MEMO_PROVIDER inconnu : {provider!r}")
    return writers[provider]()


def generate_credit_memo() -> GenerateCreditMemo:
    return GenerateCreditMemo(build_memo_writer())
