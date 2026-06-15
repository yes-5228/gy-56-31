from django.db.models import Prefetch
from rest_framework import viewsets
from rest_framework.response import Response

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

    def _refresh_route_after_action(self, booking):
        route_queryset = TravelRoute.objects.with_annotations()
        refreshed_route = route_queryset.filter(pk=booking.route_id).first()
        if refreshed_route:
            booking.route = refreshed_route

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code == 201:
            booking = Booking.objects.get(pk=response.data["id"])
            self._refresh_route_after_action(booking)
            serializer = self.get_serializer(booking)
            return Response(serializer.data, status=201)
        return response

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        old_route_id = instance.route_id
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        new_route_id = serializer.instance.route_id

        route_ids = {old_route_id, new_route_id}
        for rid in route_ids:
            if rid:
                TravelRoute.objects.filter(pk=rid).update(pk=rid)

        booking = Booking.objects.get(pk=serializer.instance.pk)
        self._refresh_route_after_action(booking)
        serializer = self.get_serializer(booking)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        route_id = instance.route_id
        self.perform_destroy(instance)
        if route_id:
            TravelRoute.objects.filter(pk=route_id).update(pk=route_id)
        return Response(status=204)
