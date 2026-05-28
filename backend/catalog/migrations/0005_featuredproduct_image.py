from django.db import migrations, models
from django.core.files.base import ContentFile
from pathlib import Path


def copy_product_images(apps, schema_editor):
    FeaturedProduct = apps.get_model('catalog', 'FeaturedProduct')
    for item in FeaturedProduct.objects.filter(active=True):
        if item.product and item.product.image and not item.image:
            try:
                img_path = item.product.image.path
                name = item.product.image.name
                with open(img_path, 'rb') as f:
                    item.image.save(
                        f'featured_{item.product.slug}.jpg',
                        ContentFile(f.read()),
                        save=True
                    )
            except Exception:
                pass


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0004_featuredproduct'),
    ]

    operations = [
        migrations.AddField(
            model_name='featuredproduct',
            name='image',
            field=models.ImageField(blank=True, help_text='Deixe vazio para usar a imagem do produto', upload_to='featured/', verbose_name='Imagem'),
        ),
        migrations.RunPython(copy_product_images, migrations.RunPython.noop),
    ]
