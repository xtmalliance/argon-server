
from django.urls import path
from . import views as scd_auth_views

urlpatterns = [
    path('v1/flights/(?P<flight_id>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', scd_auth_views.SCDAuthTest.as_view()),    
]