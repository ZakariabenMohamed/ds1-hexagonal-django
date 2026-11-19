from django.urls import path

from loans import api, views

app_name = "loans"

urlpatterns = [
    path("", views.apply_view, name="apply"),
    path("demandes/", views.list_view, name="list"),
    path("demandes/<int:application_id>/", views.detail_view, name="detail"),
    path("api/applications/", api.applications_endpoint, name="api-applications"),
    path("api/applications/<int:application_id>/", api.application_endpoint, name="api-application"),
]
