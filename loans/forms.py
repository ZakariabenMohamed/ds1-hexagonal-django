from django import forms


class LoanApplicationForm(forms.Form):
    """Formulaire de saisie. Les règles métier (bornes, etc.) restent dans le domaine."""

    applicant_name = forms.CharField(label="Nom du demandeur", max_length=120)
    applicant_reference = forms.CharField(label="Référence client", max_length=40)
    amount = forms.DecimalField(label="Montant demandé (TND)", decimal_places=3, max_digits=12)
    duration_months = forms.IntegerField(label="Durée (mois)")
    monthly_income = forms.DecimalField(label="Revenu mensuel (TND)", decimal_places=3, max_digits=12)
