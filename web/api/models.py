from django.db import models as models
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.utils import timezone

# TimeStampedModelInstance class
class TimeStampedModelInstance(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

# StationLocation model
class StationLocation(TimeStampedModelInstance):
    geolocation = gis_models.PointField()
    depth = models.FloatField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)

    def get_station(self):
        return self.content_object
    
    def __str__(self):
        return '{}: {} {}'.format(self.content_object, self.geolocation.y, self.geolocation.x)

# Station model
class Station(models.Model):
    name = models.CharField(max_length=100, unique=True)
    full_name = models.CharField(max_length=200, null=True, blank=True)
    locations = GenericRelation(StationLocation, related_query_name='station')

    def set_location(self, latitude, longitude, start_time, end_time=None, depth=None, comment=None):
        if end_time is not None:
            if end_time == start_time:
                raise ValueError('start and end time must not be identical')
            elif end_time < start_time:
                raise ValueError('end_time must be greater than or equal to start_time')
        
        if self.locations.filter(start_time=start_time).exists():
            raise ValueError('A location already exists at the given start_time')

        # Create a new Point object for the geolocation
        geolocation = Point(longitude, latitude, srid=4326)
 
        # If less recent, set the end_time to the start_time of the successor location
        successor = self.locations.filter(start_time__gt=start_time).order_by('start_time').first()

        if successor is not None:
            if end_time is None:
                end_time = successor.start_time
            if end_time > successor.start_time:
                raise ValueError('end_time must be less than or equal to the start_time of the successor location')
            
        # If more recent, close any currently "open" (end_time is None) locations by setting their end_time to the new start_time
        self.locations.filter(start_time__lt=start_time).filter(end_time__isnull=True).update(end_time=start_time)

        # Create a new StationLocation linked to this Station
        StationLocation.objects.create(
            content_object=self,
            geolocation=geolocation,
            depth=depth,
            start_time=start_time,
            end_time=end_time,
            comment=comment
        )

    def get_location(self, timestamp=None):
        if timestamp is None:
            timestamp = timezone.now()

        locations = self.locations.filter(
            Q(end_time__gte=timestamp) | Q(end_time__isnull=True),
            start_time__lte=timestamp
        ).order_by('-start_time')

        if locations.exists():
            return locations.first()
        else:
            return None

    @classmethod
    def distances(cls, latitude, longitude, timestamp):
        from django.contrib.gis.db.models.functions import Distance

        # Create a Point object from the latitude and longitude
        geolocation = Point(longitude, latitude, srid=4326)

        return StationLocation.objects.filter(
            Q(end_time__gte=timestamp) | Q(end_time__isnull=True),
            start_time__lte=timestamp
        ).annotate(distance=Distance('geolocation', geolocation)).order_by('distance')


    @classmethod
    def nearest_location(cls, latitude, longitude, timestamp=None):
        if timestamp is None:
            timestamp = timezone.now()

        distances = cls.distances(latitude, longitude, timestamp)

        if distances.exists():
            return distances.first()
        else:
            return None
        

    def __str__(self):
        return self.name
