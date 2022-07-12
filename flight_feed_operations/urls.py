from django.urls import path
from . import views as flight_feed_views
urlpatterns = [

    path('set_air_traffic', flight_feed_views.set_air_traffic),
    path('get_air_traffic', flight_feed_views.get_air_traffic),
    path('start_opensky_feed', flight_feed_views.start_opensky_feed),

]