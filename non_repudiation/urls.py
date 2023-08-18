from django.urls import path

from . import views

urlpatterns = [
    path("public_keys/", views.PublicKeyList.as_view(), name="public_keys"),
    path("public_keys/<uuid:pk>/", views.PublicKeyDetail.as_view(), name="public_keys"),
]
