from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='carouselslide',
            name='image',
            field=models.ImageField(blank=True, upload_to='carousel/', verbose_name='Imagem'),
        ),
        migrations.AlterField(
            model_name='carouselslide',
            name='image_url',
            field=models.URLField(blank=True, help_text='Usado somente se nenhuma imagem for enviada acima', max_length=500, verbose_name='URL da Imagem'),
        ),
    ]
