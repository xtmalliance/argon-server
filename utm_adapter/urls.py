from django.urls import path

from flight_declaration_operations import views as flight_declaration_views
from flight_feed_operations import views as flight_feed_views
from rid_operations import views as rid_views
from scd_operations import views as scd_views
from uss_operations import views as uss_views

urlpatterns = [
    # RID Operations endpoints
    path("ping", flight_feed_views.ping),
    path("network_remote_id/capabilities", rid_views.get_rid_capabilities),
    path("network_remote_id/set_telemetry", flight_feed_views.set_telemetry),
    path("network_remote_id/uss/flights/<uuid:flight_id>/details", uss_views.get_uss_flight_details),
    path("network_remote_id/uss/flights", uss_views.get_uss_flights),
    # Flight Declaration Operations endpoints
    path("flight_declaration", flight_declaration_views.FlightDeclarationCreateList.as_view()),
    path("flight_declaration/capabilities", scd_views.scd_capabilities),
    path(
        "flight_declaration_state/<uuid:pk>",
        flight_declaration_views.FlightDeclarationStateUpdate.as_view(),
    ),
    path("traffic_information", flight_feed_views.traffic_information_discovery_view),
]
