from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance

from dateutil import parser
from dateutil.tz import tzutc


def parse_datetime(iso_string):
    try:
        dt = parser.parse(iso_string)
        # If no timezone is specified, assume UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tzutc())
        return dt
    except Exception as e:
        return None


def find_nearest(model_class, latitude, longitude, given_time):
    point = Point(longitude, latitude, srid=4326)  # WGS84
    queryset = model_class.objects.annotate(
        distance=Distance('geolocations__coordinates', point)
    ).filter(
        geolocations__start_timestamp__lte=given_time,
        geolocations__end_timestamp__gte=given_time
    ).order_by('distance')
    
    nearest = queryset.first() if queryset.exists() else None
    
    if nearest:
        related_geolocation = nearest.geolocations.get(
            start_timestamp__lte=given_time,
            end_timestamp__gte=given_time
        )
        comments = related_geolocation.comments if related_geolocation else None
        return {
            'instance': nearest,
            'distance': nearest.distance.m,
            'comments': comments
        }

    return None