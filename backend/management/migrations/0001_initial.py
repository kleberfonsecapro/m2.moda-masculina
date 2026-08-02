# Generated migration
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('orders', '0006_order_shipping'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderStatusHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Pendente'), ('confirmed', 'Confirmado'), ('processing', 'Em Preparação'), ('shipped', 'Enviado'), ('delivered', 'Entregue'), ('cancelled', 'Cancelado')], max_length=20, verbose_name='Status')),
                ('notes', models.TextField(blank=True, verbose_name='Observações')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Data/Hora')),
                ('changed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Alterado por')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='history', to='orders.order', verbose_name='Pedido')),
            ],
            options={
                'verbose_name': 'Histórico de Status',
                'verbose_name_plural': 'Histórico de Status',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Shipment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tracking_code', models.CharField(blank=True, max_length=50, verbose_name='Código de Rastreio')),
                ('label_pdf', models.FileField(blank=True, upload_to='shipping/labels/', verbose_name='Etiqueta (PDF)')),
                ('dispatched_at', models.DateTimeField(blank=True, null=True, verbose_name='Despachado em')),
                ('delivered_at', models.DateTimeField(blank=True, null=True, verbose_name='Entregue em')),
                ('notes', models.TextField(blank=True, verbose_name='Observações do Despacho')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('order', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='shipment', to='orders.order', verbose_name='Pedido')),
            ],
            options={
                'verbose_name': 'Despacho',
                'verbose_name_plural': 'Despachos',
            },
        ),
    ]