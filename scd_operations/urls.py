
from django.urls import path, re_path
from . import views as scd_auth_views

urlpatterns = [
    re_path('v1/flights/(?P<flight_id>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', scd_auth_views.SCDAuthTest),    
    re_path('v1/clear_area_requests', scd_auth_views.SCDClearAreaRequest),    
    path('v1/status', scd_auth_views.SCDTestStatus),    
]