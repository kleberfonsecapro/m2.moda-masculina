from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_alter_order_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='cpf',
            field=models.CharField(blank=True, default='', max_length=14, verbose_name='CPF'),
        ),
    ]
