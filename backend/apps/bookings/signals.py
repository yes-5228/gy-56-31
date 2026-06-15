from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Booking


@receiver(post_save, sender=Booking)
def _invalidate_route_cache_on_save(sender, instance, **kwargs):
    route = getattr(instance, "route", None)
    if route and route.pk:
        route.clear_calculation_cache()


@receiver(post_delete, sender=Booking)
def _invalidate_route_cache_on_delete(sender, instance, **kwargs):
    route = getattr(instance, "route", None)
    if route and route.pk:
        route.clear_calculation_cache()
