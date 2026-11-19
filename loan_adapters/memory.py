"""Adaptateur de persistance en mémoire (aucune base de données).

Il implémente ``LoanRepositoryPort`` avec un simple dictionnaire. Il sert aux
tests rapides et à la démonstration : le cœur ne voit pas la différence avec
l'adaptateur Django ORM.
"""
from __future__ import annotations

import itertools
from dataclasses import replace

from loan_core.domain.models import LoanApplication


class InMemoryLoanRepository:
    def __init__(self) -> None:
        self._items: dict[int, LoanApplication] = {}
        self._ids = itertools.count(1)

    def save(self, application: LoanApplication) -> LoanApplication:
        application_id = application.id if application.id is not None else next(self._ids)
        saved = replace(application, id=application_id)
        self._items[application_id] = saved
        return saved

    def get(self, application_id: int) -> LoanApplication | None:
        return self._items.get(application_id)

    def list_recent(self, limit: int = 50) -> list[LoanApplication]:
        ordered = sorted(self._items.values(), key=lambda a: (a.created_at, a.id or 0), reverse=True)
        return ordered[:limit]
