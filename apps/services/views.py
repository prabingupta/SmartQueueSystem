"""Read-only service directory API, scoped to a single office."""
from rest_framework import generics
from rest_framework.permissions import AllowAny

from .models import Service
from .serializers import ServiceSerializer


class ServiceListView(generics.ListAPIView):
    """Requires ?office=<public_id> — services always belong to exactly one office."""
    serializer_class = ServiceSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = Service.objects.filter(is_active=True).select_related("office")
        office = self.request.query_params.get("office")
        if office:
            qs = qs.filter(office__public_id=office)
        return qs


class ServiceDetailView(generics.RetrieveAPIView):
    serializer_class = ServiceSerializer
    permission_classes = [AllowAny]
    queryset = Service.objects.filter(is_active=True)
    lookup_field = "public_id"
