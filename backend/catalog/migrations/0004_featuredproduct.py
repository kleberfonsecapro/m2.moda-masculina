from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0003_category_featured'),
    ]

    operations = [
        migrations.CreateModel(
            name='FeaturedProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(blank=True, help_text='Ex: "Lançamento", "Mais Vendido"', max_length=100, verbose_name='Rótulo')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Ordem')),
                ('active', models.BooleanField(default=True, verbose_name='Ativo')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='featured_items', to='catalog.product', verbose_name='Produto')),
            ],
            options={
                'verbose_name': 'Produto em Destaque',
                'verbose_name_plural': 'Produtos em Destaque',
                'ordering': ['order'],
            },
        ),
    ]
