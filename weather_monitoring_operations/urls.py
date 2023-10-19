from django.urls import path

from . import views as weather_monitoring_views

urlpatterns = [
    path("get_weather/", weather_monitoring_views.get_weather_data, name="get_weather"),
]