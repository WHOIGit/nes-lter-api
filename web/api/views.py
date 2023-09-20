from rest_framework import viewsets, permissions

from api.models import Station, StationLocation
from api.serializers import StationSerializer, StationLocationSerializer


class StationViewSet(viewsets.ModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
