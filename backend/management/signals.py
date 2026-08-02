from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from orders.models import Order
from .models import OrderStatusHistory


User = get_user_model()


def get_current_user():
    """Tenta obter o usuário atual via middleware (request)."""
    from django.contrib.auth.middleware import get_user
    from django.utils.deprecation import MiddlewareMixin
    # Será preenchido pelo middleware CurrentUserMiddleware
    return getattr(get_current_user, '_current_user', None)


class CurrentUserMiddleware:
    """Middleware para disponibilizar usuário atual em signals."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        get_current_user._current_user = request.user if request.user.is_authenticated else None
        response = self.get_response(request)
        get_current_user._current_user = None
        return response


@receiver(pre_save, sender=Order)
def track_order_status_change(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = Order.objects.get(pk=instance.pk)
            if old.status != instance.status:
                user = get_current_user()
                OrderStatusHistory.objects.create(
                    order=instance,
                    status=instance.status,
                    changed_by=user if user and user.is_authenticated else None,
                    notes=f'Status alterado: {old.get_status_display()} → {instance.get_status_display()}'
                )
        except Order.DoesNotExist:
            pass