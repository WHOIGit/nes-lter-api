from django.urls import include, path
from rest_framework import routers
from rest_framework.authtoken.views import obtain_auth_token

from api import views


router = routers.DefaultRouter()
router.register(r'stations', views.StationViewSet)
router.register(r'nearest-station', views.NearestStationViewSet, basename='nearest-station')


# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    path('nearest-station-csv/', views.NearestStationCsv.as_view(), name='nearest-station-csv'),
    path('station-list', views.StationList.as_view(), name='station-list'),
]