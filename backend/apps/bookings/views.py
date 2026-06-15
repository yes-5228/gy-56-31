from django.db.models import Prefetch
from rest_framework import viewsets

from apps.routes.calculation_service import RouteCalculationService
from apps.routes.models import TravelRoute
from .models import Booking
from .serializers import BookingSerializer


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer

    def get_queryset(self):
        route_queryset = TravelRoute.objects.with_annotations().all()
        queryset = Booking.objects.prefetch_related(
            Prefetch("route", queryset=route_queryset)
        ).all()
        route_id = self.request.query_params.get("route")
        status = self.request.query_params.get("status")
        if route_id:
            queryset = queryset.filter(route_id=route_id)
        if status:
            queryset = queryset.filter(status=status)
        return queryset
