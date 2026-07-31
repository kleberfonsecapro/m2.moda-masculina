# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0011_newsletter'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='secondary_image',
            field=models.ImageField(blank=True, help_text='Mostrada ao passar o mouse sobre o produto', upload_to='products/%Y/%m/', verbose_name='Imagem Secundária'),
        ),
    ]
