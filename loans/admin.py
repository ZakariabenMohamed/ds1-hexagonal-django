from django.contrib import admin

from loans.models import LoanApplicationRecord


@admin.register(LoanApplicationRecord)
class LoanApplicationRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "applicant_name", "amount", "duration_months", "decision_status", "created_at")
    list_filter = ("decision_status",)
    search_fields = ("applicant_name", "applicant_reference")
