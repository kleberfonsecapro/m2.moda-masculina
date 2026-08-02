from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'price', 'quantity']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'full_name', 'cpf', 'status', 'total',
        'created_at', 'updated_at'
    ]
    list_filter = ['status', 'created_at']
    list_editable = ['status']
    search_fields = ['full_name', 'email', 'cpf', 'user__username']
    inlines = [OrderItemInline]
    readonly_fields = ['full_name', 'email', 'phone', 'cpf', 'address', 'city', 'state', 'zip_code',
                       'shipping_method', 'shipping_cost']

    def has_add_permission(self, request):
        return False
