"""Erreurs de la couche application (orchestration)."""


class ApplicationError(Exception):
    """Racine des erreurs de la couche application."""


class ApplicationNotFound(ApplicationError):
    """Aucune demande ne correspond à l'identifiant fourni."""


class ScoringUnavailable(ApplicationError):
    """Le service de scoring externe ne répond pas.

    Les adaptateurs de scoring lèvent cette erreur : le cœur n'a ainsi jamais
    besoin de connaître les erreurs propres à une technologie (HTTP, SOAP, ...).
    """


class MemoUnavailable(ApplicationError):
    """L'assistant de rédaction du mémo ne répond pas."""
