from django.db import models
from django.conf import settings
from orders.models import Order


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='history',
        verbose_name='Pedido'
    )
    status = models.CharField(
        'Status', max_length=20, choices=Order.STATUS_CHOICES
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='Alterado por'
    )
    notes = models.TextField('Observações', blank=True)
    created_at = models.DateTimeField('Data/Hora', auto_now_add=True)

    class Meta:
        verbose_name = 'Histórico de Status'
        verbose_name_plural = 'Histórico de Status'
        ordering = ['-created_at']

    def __str__(self):
        return f'#{self.order.id} → {self.get_status_display()} ({self.created_at:%d/%m/%Y %H:%M})'


class Shipment(models.Model):
    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name='shipment',
        verbose_name='Pedido'
    )
    tracking_code = models.CharField('Código de Rastreio', max_length=50, blank=True)
    label_pdf = models.FileField('Etiqueta (PDF)', upload_to='shipping/labels/', blank=True)
    dispatched_at = models.DateTimeField('Despachado em', null=True, blank=True)
    delivered_at = models.DateTimeField('Entregue em', null=True, blank=True)
    notes = models.TextField('Observações do Despacho', blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Despacho'
        verbose_name_plural = 'Despachos'

    def __str__(self):
        return f'Despacho #{self.order.id} - {self.tracking_code or "sem rastreio"}'

    @property
    def is_dispatched(self):
        return self.dispatched_at is not None

    @property
    def is_delivered(self):
        return self.delivered_at is not None