from rest_framework.serializers import HyperlinkedModelSerializer, RelatedField, FloatField

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


class StationLocationSerializer(HyperlinkedModelSerializer):
    geolocation = GeolocationField(read_only=True)

    class Meta:
        model = StationLocation
        fields = ['id', 'geolocation', 'depth', 'start_time', 'end_time', 'comment']


class StationLocationWithDistanceSerializer(StationLocationSerializer):
    distance = FloatField(read_only=True)

    class Meta:
        model = Station
        fields = '__all__'