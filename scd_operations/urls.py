from django.urls import path, re_path

from . import views as scd_auth_views

urlpatterns = [
    # SCD Test URLS
    path("v1/flights/<uuid:operation_id>", scd_auth_views.SCDAuthTest),
    re_path("v1/clear_area_requests", scd_auth_views.SCDClearAreaRequest),
    path("v1/status", scd_auth_views.SCDTestStatus),
    path("v1/capabilities", scd_auth_views.SCDTestCapabilities),
]
