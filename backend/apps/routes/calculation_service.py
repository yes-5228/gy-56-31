from decimal import Decimal
from typing import TYPE_CHECKING

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
