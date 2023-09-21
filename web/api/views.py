from datetime import timezone
from rest_framework import viewsets, permissions

from api.models import Station, StationLocation
from api.serializers import StationSerializer, StationLocationWithDistanceSerializer
from api.utils import parse_datetime_utc


class StationViewSet(viewsets.ModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class NearestStationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StationLocation.objects.all()
    serializer_class = StationLocationWithDistanceSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        latitude = self.request.query_params.get('latitude', None)
        longitude = self.request.query_params.get('longitude', None)
        timestamp = self.request.query_params.get('timestamp', None)

        if latitude is None or longitude is None:
            return StationLocation.objects.none()
        
        if timestamp is None:
            timestamp = timezone.now()
        else:
            timestamp = parse_datetime_utc(timestamp)
        
        latitude = float(latitude)
        longitude = float(longitude)

        return [ Station.nearest_location(latitude, longitude, timestamp) ]
