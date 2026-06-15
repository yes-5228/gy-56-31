from decimal import Decimal
from typing import TYPE_CHECKING

from django.db.models import Case, DecimalField, F, IntegerField, OuterRef, Subquery, Sum, When, Value
from django.db.models.functions import Coalesce, Round

if TYPE_CHECKING:
    from .models import TravelRoute


class RouteCalculationService:
    @classmethod
    def calculate_ticket_total(cls, route: "TravelRoute") -> Decimal:
        return sum(stop.attraction.ticket_price for stop in route.stops.select_related("attraction"))

    @classmethod
    def calculate_estimated_cost(cls, route: "TravelRoute") -> Decimal:
        return route.base_cost + route.guide_fee + cls.calculate_ticket_total(route)

    @classmethod
    def calculate_enrolled_count(cls, route: "TravelRoute") -> int:
        return sum(booking.party_size for booking in route.bookings.exclude(status="cancelled"))

    @classmethod
    def calculate_group_progress(cls, route: "TravelRoute") -> int:
        if route.min_group_size == 0:
            return 100
        enrolled = cls.calculate_enrolled_count(route)
        return min(round(enrolled / route.min_group_size * 100), 100)

    @classmethod
    def calculate_all(cls, route: "TravelRoute") -> dict:
        ticket_total = cls.calculate_ticket_total(route)
        estimated_cost = route.base_cost + route.guide_fee + ticket_total
        enrolled_count = sum(booking.party_size for booking in route.bookings.exclude(status="cancelled"))
        if route.min_group_size == 0:
            group_progress = 100
        else:
            group_progress = min(round(enrolled_count / route.min_group_size * 100), 100)
        return {
            "ticket_total": ticket_total,
            "estimated_cost": estimated_cost,
            "enrolled_count": enrolled_count,
            "group_progress": group_progress,
        }

    @staticmethod
    def _build_ticket_total_subquery(route_outer_ref="pk", prefix=""):
        from .models import RouteStop

        return Coalesce(
            Subquery(
                RouteStop.objects.filter(route=OuterRef(route_outer_ref))
                .values("route")
                .annotate(total=Sum("attraction__ticket_price"))
                .values("total"),
                output_field=DecimalField(max_digits=10, decimal_places=2),
            ),
            Value(0, output_field=DecimalField(max_digits=10, decimal_places=2)),
            output_field=DecimalField(max_digits=10, decimal_places=2),
        )

    @staticmethod
    def _build_enrolled_count_subquery(route_outer_ref="pk", prefix=""):
        from apps.bookings.models import Booking

        return Coalesce(
            Subquery(
                Booking.objects.filter(route=OuterRef(route_outer_ref))
                .exclude(status="cancelled")
                .values("route")
                .annotate(total=Sum("party_size"))
                .values("total"),
                output_field=IntegerField(),
            ),
            Value(0, output_field=IntegerField()),
            output_field=IntegerField(),
        )

    @classmethod
    def build_annotations(cls, route_outer_ref="pk", prefix=""):
        ticket_total_field = f"{prefix}_annotated_ticket_total"
        enrolled_count_field = f"{prefix}_annotated_enrolled_count"
        estimated_cost_field = f"{prefix}_annotated_estimated_cost"
        group_progress_field = f"{prefix}_annotated_group_progress"
        temp_group_progress_field = f"{prefix}_annotated_group_progress_temp"

        base_cost_field = f"{prefix}base_cost" if prefix else "base_cost"
        guide_fee_field = f"{prefix}guide_fee" if prefix else "guide_fee"
        min_group_size_field = f"{prefix}min_group_size" if prefix else "min_group_size"

        step1 = {}
        step1[ticket_total_field] = cls._build_ticket_total_subquery(route_outer_ref, prefix)
        step1[enrolled_count_field] = cls._build_enrolled_count_subquery(route_outer_ref, prefix)

        step2 = {}
        step2[estimated_cost_field] = (
            F(base_cost_field) + F(guide_fee_field) + F(ticket_total_field)
        )
        step2[temp_group_progress_field] = Case(
            When(**{min_group_size_field: 0}, then=Value(100, output_field=IntegerField())),
            default=Round(
                F(enrolled_count_field) * Value(100) / F(min_group_size_field),
                output_field=IntegerField(),
            ),
            output_field=IntegerField(),
        )

        step3 = {}
        step3[group_progress_field] = Case(
            When(**{f"{temp_group_progress_field}__gt": 100}, then=Value(100, output_field=IntegerField())),
            default=F(temp_group_progress_field),
            output_field=IntegerField(),
        )

        return step1, step2, step3
