"""Read-only office directory API. Citizens browse this while booking a token."""
from rest_framework import generics
from rest_framework.permissions import AllowAny

from .models import Office
from .serializers import OfficeSerializer


class OfficeListView(generics.ListAPIView):
    """Supports ?office_type=passport&district=<public_id> filtering."""
    serializer_class = OfficeSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = Office.objects.filter(is_active=True).select_related("district")
        office_type = self.request.query_params.get("office_type")
        district = self.request.query_params.get("district")
        if office_type:
            qs = qs.filter(office_type=office_type)
        if district:
            qs = qs.filter(district__public_id=district)
        return qs


class OfficeDetailView(generics.RetrieveAPIView):
    serializer_class = OfficeSerializer
    permission_classes = [AllowAny]
    queryset = Office.objects.filter(is_active=True).select_related("district")
    lookup_field = "public_id"
