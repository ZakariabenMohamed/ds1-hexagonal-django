"""Modèle Django : détail d'infrastructure, invisible pour le cœur.

Ce modèle n'est PAS l'entité du domaine. ``LoanApplication`` (dans loan_core)
est l'entité métier ; ``LoanApplicationRecord`` n'est que sa forme stockée.
"""
from django.db import models


class LoanApplicationRecord(models.Model):
    STATUS_CHOICES = [
        ("APPROVED", "Accepté"),
        ("REJECTED", "Refusé"),
        ("MANUAL_REVIEW", "À examiner"),
    ]

    applicant_name = models.CharField(max_length=120)
    applicant_reference = models.CharField(max_length=40)
    amount = models.DecimalField(max_digits=12, decimal_places=3)
    duration_months = models.PositiveSmallIntegerField()
    monthly_income = models.DecimalField(max_digits=12, decimal_places=3)
    credit_score = models.PositiveSmallIntegerField(null=True, blank=True)
    decision_status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    decision_reasons = models.JSONField(default=list)
    monthly_payment = models.DecimalField(max_digits=12, decimal_places=3)
    debt_ratio = models.DecimalField(max_digits=6, decimal_places=4)
    created_at = models.DateTimeField()

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"#{self.pk} {self.applicant_name} — {self.decision_status}"
