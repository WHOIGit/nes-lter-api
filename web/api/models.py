from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from django.utils import timezone
from django.contrib.gis.db.models.functions import Distance
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType

class GeoLocatedObject(models.Model):
    class Meta:
        abstract = True

    geolocations = GenericRelation('GeoLocation')

    def set_coordinates(self, latitude, longitude, start_time, end_time):
        GeoLocation.objects.create(
            content_object=self,
            coordinates=Point(longitude, latitude),
            start_timestamp=start_time,
            end_timestamp=end_time
        )

    def get_coordinates_at_time(self, given_time):
        return GeoLocation.get_coordinates_at_time(self, given_time)

class Station(GeoLocatedObject):
    name = models.CharField(max_length=255)

class GeoLocation(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    coordinates = gis_models.PointField()
    start_timestamp = models.DateTimeField()
    end_timestamp = models.DateTimeField()

    @classmethod
    def get_coordinates_at_time(cls, content_object, given_time):
        queryset = cls.objects.filter(
            content_object=content_object,
            start_timestamp__lte=given_time,
            end_timestamp__gte=given_time
        )
        return [(obj.coordinates.y, obj.coordinates.x, obj.start_timestamp, obj.end_timestamp) for obj in queryset]

def find_nearest(model_class, latitude, longitude, given_time):
    point = Point(longitude, latitude, srid=4326)  # WGS84
    queryset = model_class.objects.annotate(
        distance=Distance('geolocations__coordinates', point)
    ).filter(
        geolocations__start_timestamp__lte=given_time,
        geolocations__end_timestamp__gte=given_time
    ).order_by('distance')

    return queryset.first() if queryset.exists() else None
