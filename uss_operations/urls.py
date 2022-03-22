"""flight_blender URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from flight_feed_operations import views as flight_feed_views



urlpatterns = [
    # USS Details Urls
    # This end point is used when op-intent details is used by the USS: https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/astm-utm/Protocol/cb7cf962d3a0c01b5ab12502f5f54789624977bf/utm.yaml#section/Authentication 
    # re_path('uss/v1/operational_intents/', scd_auth_views.USSUpdateOpIntDetails),    
    # re_path('uss/v1/operational_intents/(?P<flight_id>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', scd_auth_views.USSOpIntDetails),    
    # re_path('uss/v1/operational_intents/(?P<flight_id>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/telemetry', scd_auth_views.USSOpIntDetails),      
    # re_path('uss/v1/operational_intents/', scd_auth_views.USSOpIntDetails),    

]