"""Adaptateur primaire n°1 : pages HTML.

Une vue traduit une requête HTTP en commande, appelle un cas d'usage et
affiche le résultat. Aucune règle métier ici.
"""
from __future__ import annotations

from django.http import Http404
from django.shortcuts import redirect, render

from loan_core.application.errors import ApplicationNotFound
from loan_core.application.use_cases import SubmitLoanCommand
from loan_core.domain.errors import InvalidLoanRequest
from loans import composition
from loans.forms import LoanApplicationForm


def apply_view(request):
    if request.method == "POST":
        form = LoanApplicationForm(request.POST)
        if form.is_valid():
            command = SubmitLoanCommand(
                applicant_name=form.cleaned_data["applicant_name"],
                applicant_reference=form.cleaned_data["applicant_reference"],
                amount=form.cleaned_data["amount"],
                duration_months=form.cleaned_data["duration_months"],
                monthly_income=form.cleaned_data["monthly_income"],
            )
            try:
                application = composition.submit_loan_application().execute(command)
            except InvalidLoanRequest as error:
                form.add_error(None, str(error))
            else:
                return redirect("loans:detail", application_id=application.id)
    else:
        form = LoanApplicationForm()
    return render(request, "loans/apply.html", {"form": form})


def detail_view(request, application_id: int):
    try:
        application = composition.get_loan_application().execute(application_id)
    except ApplicationNotFound as error:
        raise Http404(str(error)) from error
    context = {
        "application": application,
        "debt_ratio_percent": f"{application.decision.debt_ratio * 100:.1f}".replace(".", ","),
        "memo": composition.generate_credit_memo().execute(application),
    }
    return render(request, "loans/detail.html", context)


def list_view(request):
    applications = composition.list_loan_applications().execute()
    return render(request, "loans/list.html", {"applications": applications})
