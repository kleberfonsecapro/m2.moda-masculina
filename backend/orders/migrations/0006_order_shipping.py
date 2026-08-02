from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0005_order_cpf'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='shipping_cost',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Custo do Frete'),
        ),
        migrations.AddField(
            model_name='order',
            name='shipping_method',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='Método de Envio'),
        ),
    ]
