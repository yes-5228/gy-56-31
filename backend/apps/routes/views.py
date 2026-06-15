from rest_framework import viewsets
from rest_framework.response import Response

from .models import TravelRoute
from .serializers import TravelRouteSerializer


class TravelRouteViewSet(viewsets.ModelViewSet):
    serializer_class = TravelRouteSerializer

    def get_queryset(self):
        queryset = (
            TravelRoute.objects.with_annotations()
            .prefetch_related("stops__attraction")
            .all()
        )
        status = self.request.query_params.get("status")
        city = self.request.query_params.get("city")
        if status:
            queryset = queryset.filter(status=status)
        if city:
            queryset = queryset.filter(city__icontains=city)
        return queryset

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.refresh_calculations()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        queryset = TravelRoute.objects.with_annotations().prefetch_related("stops__attraction")
        fresh = queryset.filter(pk=serializer.instance.pk).first()
        if fresh:
            serializer = self.get_serializer(fresh)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code == 201:
            queryset = TravelRoute.objects.with_annotations().prefetch_related("stops__attraction")
            fresh = queryset.filter(pk=response.data["id"]).first()
            if fresh:
                serializer = self.get_serializer(fresh)
                return Response(serializer.data, status=201)
        return response
