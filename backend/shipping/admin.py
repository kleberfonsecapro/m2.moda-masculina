from django.contrib import admin

from .models import ShippingConfig, ShippingRegion, ShippingRate


@admin.register(ShippingConfig)
class ShippingConfigAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Origem e Embalagem', {
            'fields': ['cep_origem', 'peso_padrao_kg', 'comprimento_cm', 'largura_cm', 'altura_cm'],
        }),
        ('Regras', {
            'fields': ['frete_gratis_acima_de', 'ativo'],
        }),
    ]

    def has_add_permission(self, request):
        if ShippingConfig.objects.exists():
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ShippingRegion)
class ShippingRegionAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cep_inicio', 'cep_fim', 'fator', 'ativo']
    list_editable = ['fator', 'ativo']
    list_filter = ['ativo']
    ordering = ['cep_inicio']
    search_fields = ['nome', 'cep_inicio', 'cep_fim']


@admin.register(ShippingRate)
class ShippingRateAdmin(admin.ModelAdmin):
    list_display = ['nome', 'peso_min_kg', 'peso_max_kg', 'valor_base', 'ativo']
    list_editable = ['peso_min_kg', 'peso_max_kg', 'valor_base', 'ativo']
    list_filter = ['ativo', 'nome']
    ordering = ['peso_min_kg', 'nome']
    search_fields = ['nome']
