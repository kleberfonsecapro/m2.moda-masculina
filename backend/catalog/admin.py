from django.contrib import admin
from django import forms
from .models import Category, Product, CarouselSlide, CarouselSettings


class CarouselSettingsForm(forms.ModelForm):
    class Meta:
        model = CarouselSettings
        fields = '__all__'


@admin.register(CarouselSlide)
class CarouselSlideAdmin(admin.ModelAdmin):
    list_display = ['order', 'title', 'label', 'active']
    list_editable = ['active']
    list_filter = ['active']
    ordering = ['order']
    search_fields = ['title', 'label', 'description']


@admin.register(CarouselSettings)
class CarouselSettingsAdmin(admin.ModelAdmin):
    form = CarouselSettingsForm

    def has_add_permission(self, request):
        if CarouselSettings.objects.exists():
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
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
