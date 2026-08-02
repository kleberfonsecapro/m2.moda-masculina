from django.contrib import admin
from .models import OrderStatusHistory, Shipment


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['order', 'status', 'changed_by', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order__id', 'order__full_name', 'notes']
    readonly_fields = ['order', 'status', 'changed_by', 'notes', 'created_at']
    ordering = ['-created_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ['order', 'tracking_code', 'dispatched_at', 'delivered_at']
    list_filter = ['dispatched_at', 'delivered_at']
    search_fields = ['order__id', 'order__full_name', 'tracking_code']
    readonly_fields = ['order', 'created_at', 'updated_at']
    fields = ['order', 'tracking_code', 'label_pdf', 'dispatched_at', 'delivered_at', 'notes', 'created_at', 'updated_at']