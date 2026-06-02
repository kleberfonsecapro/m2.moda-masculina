from django.contrib import admin
from django import forms
from django.utils.html import format_html
from .models import Category, Product, FeaturedProduct, CarouselSlide, CarouselSettings, SiteConfig


class CarouselSettingsForm(forms.ModelForm):
    class Meta:
        model = CarouselSettings
        fields = '__all__'


@admin.register(CarouselSlide)
class CarouselSlideAdmin(admin.ModelAdmin):
    list_display = ['order', 'title', 'label', 'active', 'image_preview']
    list_editable = ['active']
    list_filter = ['active']
    ordering = ['order']
    search_fields = ['title', 'label', 'description']
    list_display_links = ['title']

    fieldsets = [
        ('Conteúdo', {
            'fields': ['label', 'title', 'title_highlight', 'description'],
        }),
        ('Imagem e Links', {
            'fields': ['image', 'image_url', 'link_url', 'link_text'],
        }),
        ('Configurações', {
            'fields': ['order', 'active'],
        }),
    ]

    def image_preview(self, obj):
        src = None
        if obj.image:
            src = obj.image.url
        elif obj.image_url:
            src = obj.image_url
        if src:
            return format_html(
                '<img src="{}" style="max-height:50px;border-radius:4px" />',
                src
            )
        return '-'
    image_preview.short_description = 'Prévia'


@admin.register(FeaturedProduct)
class FeaturedProductAdmin(admin.ModelAdmin):
    list_display = ['product', 'label', 'order', 'active', 'image_preview']
    list_editable = ['label', 'order', 'active']
    list_filter = ['active']
    ordering = ['order']
    search_fields = ['product__name', 'label']
    autocomplete_fields = ['product']

    fieldsets = [
        ('Produto', {
            'fields': ['product', 'label'],
        }),
        ('Imagem', {
            'fields': ['image'],
            'description': 'Deixe vazio para usar a imagem do produto.',
        }),
        ('Configurações', {
            'fields': ['order', 'active'],
        }),
    ]

    def image_preview(self, obj):
        src = None
        if obj.image:
            src = obj.image.url
        elif obj.product.image:
            src = obj.product.image.url
        if src:
            return format_html(
                '<img src="{}" style="max-height:50px;border-radius:4px" />',
                src
            )
        return '-'
    image_preview.short_description = 'Prévia'


@admin.register(CarouselSettings)
class CarouselSettingsAdmin(admin.ModelAdmin):
    form = CarouselSettingsForm

    def has_add_permission(self, request):
        if CarouselSettings.objects.exists():
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SiteConfig)
class SiteConfigAdmin(admin.ModelAdmin):
    fieldsets = [
        ('WhatsApp', {
            'fields': ['whatsapp_number'],
        }),
        ('Redes Sociais', {
            'fields': ['instagram', 'facebook', 'youtube', 'tiktok', 'twitter'],
            'description': 'Deixe em branco as redes que não possui.',
        }),
        ('Contato', {
            'fields': ['email'],
        }),
    ]

    def has_add_permission(self, request):
        if SiteConfig.objects.exists():
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'featured', 'created_at']
    list_editable = ['featured']
    list_filter = ['featured']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'price', 'promotional_price',
        'stock', 'available', 'featured', 'created_at'
    ]
    list_filter = ['available', 'featured', 'category', 'created_at']
    list_editable = ['price', 'promotional_price', 'stock', 'available', 'featured']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    raw_id_fields = ['category']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
