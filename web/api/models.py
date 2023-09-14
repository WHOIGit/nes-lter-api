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

    def set_coordinates(self, latitude, longitude, depth, start_time, end_time, comments=None):
        GeoLocation.objects.create(
            content_object=self,
            coordinates=Point(longitude, latitude),
            depth=depth,
            comments=comments,
            start_timestamp=start_time,
            end_timestamp=end_time
        )

    def get_coordinates_at_time(self, given_time):
        return GeoLocation.get_coordinates_at_time(self, given_time)
    
    def unset_coordinates(self, given_time):
        self.geolocations.filter(
            start_timestamp__lte=given_time,
            end_timestamp__gte=given_time
        ).delete()

class Station(GeoLocatedObject):
    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.name

class GeoLocation(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    coordinates = gis_models.PointField()
    depth = models.FloatField(null=True)
    comments = models.TextField(null=True)
    start_timestamp = models.DateTimeField()
    end_timestamp = models.DateTimeField()

    @classmethod
    def get_coordinates_at_time(cls, content_object, given_time):
        queryset = cls.objects.filter(
            content_object=content_object,
            start_timestamp__lte=given_time,
            end_timestamp__gte=given_time
        )
        return [{
            'latitude': obj.coordinates.y,
            'longitude': obj.coordinates.x,
            'depth': obj.depth,
            'comments': obj.comments,
            'start_timestamp': obj.start_timestamp,
            'end_timestamp': obj.end_timestamp
        } for obj in queryset]


class Organization(models.Model):
    name = models.TextField() # e.g., "Woods Hole Oceanographic Institution"
    acronym = models.CharField(max_length=32, null=True) # e.g., "WHOI"

    def __str__(self) -> str:
        return self.acronym if self.acronym else self.name


class Person(models.Model):
    full_name = models.TextField() # e.g., "Robert Ballard"
    affiliation = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True)

    def __str__(self) -> str:
        return self.full_name


class Role(models.Model):
    name = models.CharField(max_length=128) # e.g., "Chief Scientist"

    def __str__(self) -> str:
        return self.name


class Vessel(models.Model):
    designation = models.CharField(max_length=64) # abbreviation e.g., "AR" for "Armstrong"
    name = models.TextField(null=True) # name of vessel e.g., "R/V Neil Armstrong"
    nickname = models.CharField(max_length=64, null=True) # nickname e.g., "Armstrong"
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True)

    def __str__(self) -> str:
        return self.nickname if self.nickname else self.name
    

class Cruise(models.Model):
    vessel = models.ForeignKey(Vessel, on_delete=models.CASCADE)
    name = models.CharField(max_length=64) # e.g., "AR70b"
    start_timestamp = models.DateTimeField()
    end_timestamp = models.DateTimeField(null=True)
    comments = models.TextField(null=True)

    def __str__(self) -> str:
        return self.name
    

class Cast(models.Model):
    cruise = models.ForeignKey(Cruise, on_delete=models.CASCADE, related_name="casts")
    sort_key = models.IntegerField() # e.g., 1
    name = models.CharField(max_length=64) # e.g., "1b"
    location = gis_models.PointField()
    max_depth = models.FloatField(null=True)
    start_timestamp = models.DateTimeField()
    end_timestamp = models.DateTimeField(null=True)
    comments = models.TextField(null=True)

    def __str__(self) -> str:
        return f"{self.cruise.name} {self.name}"
    
