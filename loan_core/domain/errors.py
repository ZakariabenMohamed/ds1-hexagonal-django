"""Erreurs métier. Aucune dépendance externe."""


class DomainError(Exception):
    """Racine de toutes les erreurs du domaine."""


class InvalidLoanRequest(DomainError):
    """La demande de prêt ne respecte pas les invariants métier."""
