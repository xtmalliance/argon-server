from django.utils.decorators import method_decorator
from rest_framework import generics

from auth_helper.utils import requires_scopes

from .models import PublicKey
from .serializers import PublicKeySerializer


@method_decorator(requires_scopes(["blender.read", "blender.write"]), name="dispatch")
class PublicKeyList(generics.ListCreateAPIView):
    queryset = PublicKey.objects.all()
    serializer_class = PublicKeySerializer


@method_decorator(requires_scopes(["blender.read", "blender.write"]), name="dispatch")
class PublicKeyDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = PublicKey.objects.all()
    serializer_class = PublicKeySerializer
