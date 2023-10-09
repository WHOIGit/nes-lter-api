from datetime import timezone
from io import StringIO

import pandas as pd

from django.http import HttpResponse
from django.core.exceptions import ValidationError

from rest_framework import viewsets, permissions
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import TokenAuthentication

from api.models import Station, StationLocation
from api.serializers import StationSerializer, StationLocationWithDistanceSerializer
from api.utils import parse_datetime_utc
from api.parsers.ctd.hdr import HdrFile
from api.parsers.ctd.btl import BtlFile, parse_btl

from api.workflows import add_nearest_station, station_list


class StationViewSet(viewsets.ModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class NearestStationViewSet(viewsets.ReadOnlyModelViewSet):

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


class AddNearestStations(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        timestamp_column = request.GET.get('timestamp_column', None)
        latitude_column = request.GET.get('latitude_column', None)
        longitude_column = request.GET.get('longitude_column', None)

        csv_file = request.FILES.get('csv_file', None)
        
        if not csv_file:
            return Response({"error": "No file called 'csv_file'"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Read input CSV using pandas
        try:
            input_df = pd.read_csv(csv_file)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        # add nearest station information
        try:
            output_df = add_nearest_station(input_df,
                                            timestamp_column=timestamp_column,
                                            latitude_column=latitude_column,
                                            longitude_column=longitude_column)

            return csv_response(output_df, 'nearest_station.csv')
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

          
class StationList(APIView):
    
    def get(self, request):
        timestamp = request.GET.get('timestamp', None)

        try:
            df = station_list(timestamp=timestamp)
            return csv_response(df, 'station_list.csv')
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

          
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
            hdr = HdrFile(buffer=hdr_file, parse=True)
            latitude, longitude, time = hdr.lat, hdr.lon, hdr.time

            return Response({"latitude": latitude, "longitude": longitude, "time": time})
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ParseBtlFile(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):

        btl_file = request.FILES.get('btl_file', None)

        if btl_file is None:
            return Response({"error": "No BTL data provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Read input BTL file using parse_btl
        try:
            btl = BtlFile(buffer=btl_file, parse=True)
            df = btl.to_dataframe()

            return csv_response(df, 'btl.csv')
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)