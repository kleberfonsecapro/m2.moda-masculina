from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.home, name='home'),
    path('produtos/', views.product_list, name='product_list'),
    path('produtos/<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    path('produto/<slug:slug>/', views.product_detail, name='product_detail'),
]
