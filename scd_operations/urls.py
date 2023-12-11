
from django.urls import path, re_path
from . import views as scd_auth_views

urlpatterns = [
    # SCD Test URLS
    path('v1/flights/<uuid:operation_id>', scd_auth_views.scd_auth_test),    
    re_path('v1/clear_area_requests', scd_auth_views.scd_clear_area_request),    
    path('v1/status', scd_auth_views.scd_test_status),      
    path('v1/capabilities', scd_auth_views.scd_test_capabilities),    

]