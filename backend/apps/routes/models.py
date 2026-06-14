from django.db import models

from apps.attractions.models import Attraction
from .calculation_service import RouteCalculationService


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

    class Meta:
        ordering = ["-created_at", "id"]

    def __str__(self):
        return self.title

    @property
    def ticket_total(self):
        return RouteCalculationService.calculate_ticket_total(self)

    @property
    def estimated_cost(self):
        return RouteCalculationService.calculate_estimated_cost(self)

    @property
    def enrolled_count(self):
        return RouteCalculationService.calculate_enrolled_count(self)

    @property
    def group_progress(self):
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
