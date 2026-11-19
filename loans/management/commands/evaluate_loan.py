"""Adaptateur primaire n°3 : la ligne de commande (CLI).

Même cas d'usage que les pages HTML et l'API JSON, appelé depuis un terminal :

    python manage.py evaluate_loan --name "Amine" --reference CLI-1 --amount 20000 --months 60 --income 2000
"""
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand, CommandError

from loan_core.application.use_cases import SubmitLoanCommand
from loan_core.domain.errors import InvalidLoanRequest
from loans import composition


class Command(BaseCommand):
    help = "Évalue et enregistre une demande de prêt depuis la ligne de commande."

    def add_arguments(self, parser):
        parser.add_argument("--name", required=True)
        parser.add_argument("--reference", required=True)
        parser.add_argument("--amount", required=True)
        parser.add_argument("--months", required=True, type=int)
        parser.add_argument("--income", required=True)

    def handle(self, *args, **options):
        try:
            command = SubmitLoanCommand(
                applicant_name=options["name"],
                applicant_reference=options["reference"],
                amount=Decimal(options["amount"]),
                duration_months=options["months"],
                monthly_income=Decimal(options["income"]),
            )
        except InvalidOperation as error:
            raise CommandError("Montant ou revenu non numérique.") from error
        try:
            application = composition.submit_loan_application().execute(command)
        except InvalidLoanRequest as error:
            raise CommandError(str(error)) from error

        decision = application.decision
        self.stdout.write(f"Demande #{application.id} : {decision.status.value}")
        self.stdout.write(f"  Mensualité : {decision.monthly_payment} TND ({decision.debt_ratio * 100:.1f} % du revenu)")
        for reason in decision.reasons:
            self.stdout.write(f"  - {reason}")
