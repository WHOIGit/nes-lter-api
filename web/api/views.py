from io import StringIO, BytesIO

import pandas as pd

from django.http import Http404, HttpResponse, JsonResponse
from django.utils import timezone
from django.core.exceptions import ValidationError

from rest_framework import viewsets, permissions
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import TokenAuthentication

from api.models import Station, StationLocation
from api.serializers import StationSerializer, StationLocationWithDistanceSerializer
from api.utils import parse_datetime, parse_datetime_utc
from api.parsers.ctd.hdr import HdrFile
from api.parsers.ctd.btl import BtlFile
from api.parsers.ctd.asc import parse_asc

from api.workflows import add_nearest_station, station_list


class StationViewSet(viewsets.ModelViewSet):

    queryset = Station.objects.all()
    serializer_class = StationSerializer

    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    lookup_field = 'name'
    
    def create(self, request, *args, **kwargs):
        station_name = request.data.get('name')
        if not station_name:
            return Response({"error": "name is required"}, status=status.HTTP_400_BAD_REQUEST)

        station, created = Station.objects.get_or_create(name=station_name, defaults={
            'name': station_name,
            'full_name': request.data.get('full_name')
        })

        if created:
            message = f"Station '{station_name}' created successfully."
        else:
            message = f"Station '{station_name}' already exists."

        return Response({"message": message}, status=status.HTTP_201_CREATED)

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        filter_kwargs = {self.lookup_field: self.kwargs[self.lookup_field]}
        obj = queryset.filter(**filter_kwargs).first()
        if obj is None:
            raise Http404(f"No station found with name '{filter_kwargs[self.lookup_field]}'")
        self.check_object_permissions(self.request, obj)
        return obj
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"message": f"Station '{instance.name}' deleted successfully."}, status=status.HTTP_200_OK)


class AddStationLocation(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):

        station_name = request.data.get('name', None)

        if station_name is None:
            return Response({"error": "name is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        station = Station.objects.filter(name=station_name).first()

        if station is None:
            return Response({"error": f"Station '{station_name}' not found."}, status=status.HTTP_404_NOT_FOUND)
        
        latitude = request.data.get('latitude', None)
        longitude = request.data.get('longitude', None)
        depth = request.data.get('depth', None)
        start_time = request.data.get('start_time', None)
        end_time = request.data.get('end_time', None)
        comment = request.data.get('comment', None)

        if latitude is None or longitude is None or start_time is None:
            return Response({"error": "latitude, longitude, and start_time are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            latitude = float(latitude)
            longitude = float(longitude)
            start_time = parse_datetime_utc(start_time)
            if end_time is not None:
                end_time = parse_datetime_utc(end_time)
            if depth is not None:
                depth = float(depth)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            station.set_location(latitude=latitude, longitude=longitude, start_time=start_time,
                                    end_time=end_time, depth=depth, comment=comment)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"message": f"Location for station '{station_name}' added successfully."}, status=status.HTTP_201_CREATED)


class NearestStationViewSet(viewsets.ModelViewSet):

    serializer_class = StationLocationWithDistanceSerializer

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
            if timestamp is None:
                return StationLocation.objects.none()
        
        latitude = float(latitude)
        longitude = float(longitude)
      
        return [ Station.nearest_location(latitude, longitude, timestamp) ]

    def create(self, request):
        
        # Extract data from request
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        timestamp = request.data.get('timestamp')

        if not latitude or not longitude:
            return Response({"error": "Latitude and longitude are required."}, status=status.HTTP_400_BAD_REQUEST)

        if timestamp == "":
            timestamp = timezone.now()
        else:
            timestamp = parse_datetime_utc(timestamp)
            print("timestamp", timestamp)
            if timestamp is None:
                return Response({"error": "Invalid timestamp format."}, status=status.HTTP_400_BAD_REQUEST)

        nearest_station = Station.nearest_location(float(latitude), float(longitude), timestamp)
        if nearest_station is None:
            return Response({"error": "No nearest station found."}, status=status.HTTP_404_NOT_FOUND)

        # Serialize the result for the json response
        serializer = StationLocationWithDistanceSerializer(nearest_station)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        

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
        

class ParseAscFile(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):

        asc_file = request.FILES.get('asc_file', None)

        if asc_file is None:
            return Response({"error": "No ASC data provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Read input ASC file using pandas
        try:
            buffer = BytesIO(asc_file.read())
            df = parse_asc(buffer, infer_delimiter=True)
            return csv_response(df, 'asc.csv')
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
