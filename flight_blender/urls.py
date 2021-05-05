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
    path('admin/', admin.site.urls),
    path('ping', flight_feed_views.ping),
    path('set_air_traffic', flight_feed_views.set_air_traffic),

    path('dss/', include('dss_operations.urls')),    

    path('geo_fence_ops/', include('geo_fence_operations.urls')),    
    path('flight_declaration_ops/', include('geo_fence_operations.urls')),

    
]
