"""Crée quelques demandes de démonstration (utile pour les captures d'écran)."""
from decimal import Decimal

from django.core.management.base import BaseCommand

from loan_core.application.use_cases import SubmitLoanCommand
from loans import composition

DEMO = [
    ("Amine Trabelsi", "CLI-1001", "20000", 60, "2000"),
    ("Salma Ben Ali", "CLI-1002", "35000", 48, "1800"),
    ("Youssef Gharbi", "CLI-1003", "8000", 24, "1500"),
    ("Mariem Jlassi", "CLI-1004", "60000", 84, "3500"),
    ("Hatem Mejri", "CLI-1005", "15000", 36, "900"),
    ("Nour Haddad", "CLI-9", "15000", 36, "2500"),  # score simulé moyen : examen manuel
]


class Command(BaseCommand):
    help = "Insère des demandes de prêt de démonstration via le cas d'usage."

    def handle(self, *args, **options):
        use_case = composition.submit_loan_application()
        for name, reference, amount, months, income in DEMO:
            application = use_case.execute(
                SubmitLoanCommand(name, reference, Decimal(amount), months, Decimal(income))
            )
            self.stdout.write(
                f"#{application.id} {name:<16} score={application.credit_score} "
                f"-> {application.decision.status.value}"
            )
