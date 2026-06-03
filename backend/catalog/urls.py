from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.home, name='home'),
    path('vendas/', views.sales_page, name='sales_page'),
    path('vendas/entrar/', auth_views.LoginView.as_view(
        template_name='catalog/sales_login.html',
        extra_context={'title': 'Acesso do Vendedor'},
    ), name='sales_login'),
    path('vendas/buscar/', views.sales_product_lookup, name='sales_product_lookup'),
    path('vendas/adicionar/', views.sales_add_item, name='sales_add_item'),
    path('vendas/finalizar/', views.sales_checkout, name='sales_checkout'),
    path('vendas/estoque/', views.stock_page, name='stock_page'),
    path('produtos/', views.product_list, name='product_list'),
    path('produtos/<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    path('produto/<slug:slug>/', views.product_detail, name='product_detail'),
]
