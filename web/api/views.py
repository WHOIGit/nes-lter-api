from datetime import timezone
from io import StringIO

import pandas as pd

from django.http import HttpResponse

from rest_framework import viewsets, permissions
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import TokenAuthentication

from api.models import Station, StationLocation
from api.serializers import StationSerializer, StationLocationWithDistanceSerializer
from api.utils import parse_datetime_utc
from api.parsers.ctd import parse_hdr

from api.workflows import add_nearest_station


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


def csv_response(df, filename):
    output = StringIO()
    df.to_csv(output, index=False)
    csv_content = output.getvalue()

    # Send it as a response
    response = HttpResponse(csv_content, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename={filename}'
    
    return response


class NearestStationCsv(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        csv_file = request.FILES.get('csv_file', None)
        
        if not csv_file:
            return Response({"error": "No file called 'csv_file'"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Read input CSV using pandas
        input_df = pd.read_csv(csv_file)
        
        # add nearest station information
        output_df = add_nearest_station(input_df)

        return csv_response(output_df, 'output.csv')


# view to parse a POSTed hdr file and return lat, lon, time

class ParseHdrFile(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):

        hdr_file = request.FILES.get('hdr_file', None)

        if hdr_file is None:
            return Response({"error": "No HDR data provided"}, status=status.HTTP_400_BAD_REQUEST)
    
        # Read input HDR file using parse_hdr_file
        try:
            hdr_data = hdr_file.read().decode('ISO-8859-1')
            latitude, longitude, time = parse_hdr(hdr_data)

            return Response({"latitude": latitude, "longitude": longitude, "time": time})
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
