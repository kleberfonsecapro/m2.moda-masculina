from django.urls import path

from . import views

app_name = 'shipping'

urlpatterns = [
    path('cep/', views.cep_lookup, name='cep_lookup'),
    path('calcular/', views.shipping_quote, name='quote'),
]
