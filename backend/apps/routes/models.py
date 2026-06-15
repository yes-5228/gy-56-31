from django.db import models

from apps.attractions.models import Attraction
from .calculation_service import RouteCalculationService


class TravelRouteQuerySet(models.QuerySet):
    def with_annotations(self):
        base_annotations, step2_annotations, step3_annotations = (
            RouteCalculationService.build_annotations(route_outer_ref="pk", prefix="")
        )
        return (
            self.annotate(**base_annotations)
            .annotate(**step2_annotations)
            .annotate(**step3_annotations)
        )


class TravelRouteManager(models.Manager.from_queryset(TravelRouteQuerySet)):
    pass


class TravelRoute(models.Model):
    STATUS_CHOICES = [
        ("draft", "草稿"),
        ("published", "已发布"),
        ("forming", "报名成团中"),
    ]

    title = models.CharField("线路名称", max_length=100)
    city = models.CharField("目的地城市", max_length=50)
    days = models.PositiveIntegerField("天数", default=1)
    transport = models.CharField("交通方式", max_length=80)
    hotel_level = models.CharField("住宿标准", max_length=80)
    min_group_size = models.PositiveIntegerField("最低成团人数", default=4)
    max_group_size = models.PositiveIntegerField("最多人数", default=20)
    base_cost = models.DecimalField("基础费用", max_digits=10, decimal_places=2)
    guide_fee = models.DecimalField("导游服务费", max_digits=10, decimal_places=2, default=0)
    status = models.CharField("状态", max_length=20, choices=STATUS_CHOICES, default="draft")
    attractions = models.ManyToManyField(Attraction, through="RouteStop", related_name="routes")
    description = models.TextField("行程简介", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TravelRouteManager()

    class Meta:
        ordering = ["-created_at", "id"]

    def __str__(self):
        return self.title

    _ANNOTATED_FIELDS = [
        "_annotated_ticket_total",
        "_annotated_enrolled_count",
        "_annotated_estimated_cost",
        "_annotated_group_progress",
        "_annotated_group_progress_temp",
    ]

    def clear_calculation_cache(self):
        for field in self._ANNOTATED_FIELDS:
            if hasattr(self, field):
                delattr(self, field)

    def refresh_calculations(self):
        self.clear_calculation_cache()
        fresh = (
            TravelRoute.objects.with_annotations().filter(pk=self.pk).first()
        )
        if fresh:
            for field in self._ANNOTATED_FIELDS:
                if hasattr(fresh, field):
                    setattr(self, field, getattr(fresh, field))
        return self

    @property
    def ticket_total(self):
        if hasattr(self, "_annotated_ticket_total"):
            return self._annotated_ticket_total
        return RouteCalculationService.calculate_ticket_total(self)

    @property
    def estimated_cost(self):
        if hasattr(self, "_annotated_estimated_cost"):
            return self._annotated_estimated_cost
        return RouteCalculationService.calculate_estimated_cost(self)

    @property
    def enrolled_count(self):
        if hasattr(self, "_annotated_enrolled_count"):
            return self._annotated_enrolled_count
        return RouteCalculationService.calculate_enrolled_count(self)

    @property
    def group_progress(self):
        if hasattr(self, "_annotated_group_progress"):
            return self._annotated_group_progress
        return RouteCalculationService.calculate_group_progress(self)


class RouteStop(models.Model):
    route = models.ForeignKey(TravelRoute, related_name="stops", on_delete=models.CASCADE)
    attraction = models.ForeignKey(Attraction, on_delete=models.CASCADE)
    day = models.PositiveIntegerField("第几天", default=1)
    order = models.PositiveIntegerField("当天顺序", default=1)
    note = models.CharField("安排说明", max_length=160, blank=True)

    class Meta:
        ordering = ["day", "order", "id"]
        unique_together = ("route", "day", "order")

    def __str__(self):
        return f"{self.route.title} D{self.day}-{self.order}"
