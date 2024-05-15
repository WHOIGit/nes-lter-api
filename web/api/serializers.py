from rest_framework.serializers import HyperlinkedModelSerializer, RelatedField, FloatField, CharField, SerializerMethodField

from api.models import Station, StationLocation


class GeolocatedObjectRelatedField(RelatedField):
    
    def to_representation(self, value):
        if isinstance(value, StationLocation):
            serializer = StationLocationSerializer(value)
        else:
            raise Exception('Unexpected type of geolocated object')

        return serializer.data

class GeolocationField(RelatedField):

    def to_representation(self, value):
        latitude = value.y
        longitude = value.x
        return {
            'latitude': latitude,
            'longitude': longitude
        }
    

class StationSerializer(HyperlinkedModelSerializer):
    locations = GeolocatedObjectRelatedField(many=True, read_only=True)

    class Meta:
        model = Station
        fields = ['id', 'name', 'locations']

class AbbreviatedStationSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = Station
        fields = ['id', 'name']

class StationLocationSerializer(HyperlinkedModelSerializer):
    geolocation = GeolocationField(read_only=True)

    class Meta:
        model = StationLocation
        fields = ['id', 'geolocation', 'depth', 'start_time', 'end_time', 'comment']


class DistanceField(RelatedField):

    def to_representation(self, value):
        return value.m / 1000 # convert to km

class StationField(RelatedField):

    def to_representation(self, value):
        serializer = AbbreviatedStationSerializer(value.first())

        return serializer.data


class StationLocationWithDistanceSerializer(StationLocationSerializer):
    distance = DistanceField(read_only='True')
    station = StationField(read_only='True')
    geolocation = GeolocationField(read_only='True')
    depth = FloatField(read_only='True')
    start_time = CharField(read_only='True')
    end_time = CharField(read_only='True')
    comment = CharField(read_only='True')

    latitude = FloatField(allow_null=True, required=True, help_text="Enter latitude in decimal degrees, positive is North & negative is South (e.g., 41.03)")
    longitude = FloatField(allow_null=True, required=True, help_text="Enter longitude in decimal degrees, positive is East & negative is West (e.g., -70.8833)")
    timestamp = CharField(allow_null=True, required=False, max_length=19, help_text="Enter UTC timestamp (format: YYYY-MM-DD, YYYY-MM-DDThh:mm, YYYY-MM-DDThh:mm:ss)")

    class Meta:
        model = StationLocation
        fields = ['id', 'station', 'geolocation', 'distance', 'depth', 'start_time', 'end_time',
                  'comment', 'latitude', 'longitude', 'timestamp']
