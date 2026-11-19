"""Adaptateur primaire n°2 : API JSON.

Même cas d'usage que les pages HTML, autre mode de livraison : c'est
l'intérêt de l'architecture hexagonale. L'endpoint POST est exempté de CSRF
car c'est une API de démonstration sans session ni authentification ;
une API réelle utiliserait un jeton (JWT, par exemple).
"""
from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from loan_core.application.errors import ApplicationNotFound
from loan_core.application.use_cases import SubmitLoanCommand
from loan_core.domain.errors import InvalidLoanRequest
from loan_core.domain.models import LoanApplication
from loans import composition


def application_to_dict(application: LoanApplication) -> dict:
    return {
        "id": application.id,
        "applicant": {
            "name": application.applicant.name,
            "reference": application.applicant.reference,
        },
        "request": {
            "amount": str(application.request.amount),
            "duration_months": application.request.duration_months,
            "monthly_income": str(application.request.monthly_income),
        },
        "credit_score": application.credit_score,
        "decision": {
            "status": application.decision.status.value,
            "reasons": list(application.decision.reasons),
            "monthly_payment": str(application.decision.monthly_payment),
            "debt_ratio": str(application.decision.debt_ratio),
        },
        "created_at": application.created_at.isoformat(),
    }


def _parse_command(payload: dict) -> SubmitLoanCommand:
    try:
        return SubmitLoanCommand(
            applicant_name=str(payload["applicant_name"]),
            applicant_reference=str(payload["applicant_reference"]),
            amount=Decimal(str(payload["amount"])),
            duration_months=int(payload["duration_months"]),
            monthly_income=Decimal(str(payload["monthly_income"])),
        )
    except KeyError as error:
        raise InvalidLoanRequest(f"Champ manquant : {error.args[0]}") from error
    except (InvalidOperation, ValueError, TypeError) as error:
        raise InvalidLoanRequest("Valeur numérique invalide.") from error


@csrf_exempt
@require_http_methods(["GET", "POST"])
def applications_endpoint(request):
    if request.method == "GET":
        items = composition.list_loan_applications().execute()
        return JsonResponse({"results": [application_to_dict(a) for a in items]})

    try:
        payload = json.loads(request.body or b"{}")
        if not isinstance(payload, dict):
            raise InvalidLoanRequest("Le corps doit être un objet JSON.")
        command = _parse_command(payload)
        application = composition.submit_loan_application().execute(command)
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON invalide."}, status=400)
    except InvalidLoanRequest as error:
        return JsonResponse({"error": str(error)}, status=400)
    return JsonResponse(application_to_dict(application), status=201)


@require_http_methods(["GET"])
def application_endpoint(request, application_id: int):
    try:
        application = composition.get_loan_application().execute(application_id)
    except ApplicationNotFound as error:
        return JsonResponse({"error": str(error)}, status=404)
    body = application_to_dict(application)
    memo = composition.generate_credit_memo().execute(application)
    body["memo"] = {"text": memo.text, "source": memo.source, "issues": list(memo.issues)}
    return JsonResponse(body)
