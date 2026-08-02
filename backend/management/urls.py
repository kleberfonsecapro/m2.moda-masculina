from django.urls import path
from . import views

app_name = 'management'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('pedidos/', views.OrderListView.as_view(), name='order_list'),
    path('pedidos/exportar/', views.ExportOrdersView.as_view(), name='export_orders'),
    path('pedidos/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('pedidos/<int:pk>/status/', views.OrderStatusUpdateView.as_view(), name='order_status_update'),
    path('pedidos/<int:pk>/despachar/', views.DispatchView.as_view(), name='dispatch'),
    path('financeiro/', views.FinancialView.as_view(), name='financial'),
    path('estoque/', views.StockAlertView.as_view(), name='stock_alert'),
]