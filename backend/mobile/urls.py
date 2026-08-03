from django.urls import path

from . import views

app_name = 'mobile'

urlpatterns = [
    path('', views.home, name='home'),
    path('categorias/', views.categories, name='categories'),
    path('produtos/', views.product_list, name='products'),
    path('categorias/<slug:category_slug>/', views.product_list, name='category'),
    path('produto/<slug:slug>/', views.product_detail, name='product_detail'),
    path('carrinho/', views.cart, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/sucesso/<int:order_id>/', views.order_success, name='order_success'),
    path('vendas/entrar/', views.SalesLoginView.as_view(), name='sales_login'),
    path('vendas/', views.sales_page, name='sales_page'),
    path('perfil/', views.profile, name='profile'),
]
