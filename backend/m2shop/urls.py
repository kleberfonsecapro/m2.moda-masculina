from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .admin_views import admin_logout
from mobile import views as mobile_views

admin.site.site_header = 'M2 Moda Masculina - Administração'
admin.site.site_title = 'M2 Moda Masculina'
admin.site.index_title = 'Painel de Controle'

urlpatterns = [
    path('admin/logout/', admin_logout, name='admin_logout'),
    path('admin/', admin.site.urls),
    path('', include('catalog.urls', namespace='catalog')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('orders/', include('orders.urls', namespace='orders')),
    path('frete/', include('shipping.urls', namespace='shipping')),
    path('gerencial/', include('management.urls', namespace='management')),
    path('view/mobile/', mobile_views.view_mobile, name='view_mobile'),
    path('view/desktop/', mobile_views.view_desktop, name='view_desktop'),
    path('m/', include('mobile.urls', namespace='mobile')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
