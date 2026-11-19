"""Adaptateurs du port ``ScoringEnginePort``.

IMPORTANT : ce projet n'appelle aucune vraie centrale de crédit. Le
``SimulatedCreditBureau`` produit un score déterministe à partir de la
référence client : c'est une simulation, à présenter comme telle à l'oral.
Remplacer ce fichier par un client HTTP réel ne changerait pas une ligne du cœur.
"""
from __future__ import annotations

import hashlib

from loan_core.application.errors import ScoringUnavailable

MIN_SCORE = 300
MAX_SCORE = 850


class SimulatedCreditBureau:
    """Score reproductible entre 300 et 850, dérivé d'un hash de la référence."""

    def score_for(self, applicant_reference: str) -> int:
        digest = hashlib.sha256(applicant_reference.strip().lower().encode("utf-8")).digest()
        value = int.from_bytes(digest[:4], "big")
        return MIN_SCORE + value % (MAX_SCORE - MIN_SCORE + 1)


class FixedCreditScore:
    """Retourne toujours le même score (pratique pour les tests et les démos)."""

    def __init__(self, score: int) -> None:
        self._score = score

    def score_for(self, applicant_reference: str) -> int:
        return self._score


class UnavailableCreditBureau:
    """Simule une panne du service de scoring."""

    def score_for(self, applicant_reference: str) -> int:
        raise ScoringUnavailable("Service de scoring indisponible (panne simulée).")
