from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ShippingConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cep_origem', models.CharField(help_text='CEP de onde os pedidos são enviados (apenas números)', max_length=8, verbose_name='CEP de Origem')),
                ('peso_padrao_kg', models.DecimalField(decimal_places=2, default=1.0, help_text='Peso médio da caixa com os produtos. O cálculo usa peso real OU cúbico, o que for maior.', max_digits=5, verbose_name='Peso padrão da embalagem (kg)')),
                ('comprimento_cm', models.DecimalField(decimal_places=2, default=30, max_digits=6, verbose_name='Comprimento da embalagem (cm)')),
                ('largura_cm', models.DecimalField(decimal_places=2, default=20, max_digits=6, verbose_name='Largura da embalagem (cm)')),
                ('altura_cm', models.DecimalField(decimal_places=2, default=10, max_digits=6, verbose_name='Altura da embalagem (cm)')),
                ('frete_gratis_acima_de', models.DecimalField(blank=True, decimal_places=2, help_text='Se o subtotal do pedido for maior ou igual a este valor, o frete fica grátis. Deixe vazio para nunca dar frete grátis.', max_digits=10, null=True, verbose_name='Frete grátis acima de (R$)')),
                ('ativo', models.BooleanField(default=True, help_text='Quando desativado, o cálculo de frete fica indisponível no site.', verbose_name='Ativo')),
            ],
            options={
                'verbose_name': 'Configuração de Frete',
                'verbose_name_plural': 'Configurações de Frete',
            },
        ),
        migrations.CreateModel(
            name='ShippingRate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(help_text='Ex: "Sedex", "PAC", "Retirada na loja"', max_length=100, verbose_name='Serviço de Envio')),
                ('peso_min_kg', models.DecimalField(decimal_places=2, default=0, max_digits=5, verbose_name='Peso mínimo (kg)')),
                ('peso_max_kg', models.DecimalField(decimal_places=2, default=1, max_digits=5, verbose_name='Peso máximo (kg)')),
                ('valor_base', models.DecimalField(decimal_places=2, help_text='Tarifa para esta faixa de peso. Será multiplicada pelo fator da região do CEP de destino.', max_digits=10, verbose_name='Valor base (R$)')),
                ('ativo', models.BooleanField(default=True, verbose_name='Ativo')),
            ],
            options={
                'verbose_name': 'Tarifa de Envio',
                'verbose_name_plural': 'Tarifas de Envio',
                'ordering': ['peso_min_kg', 'nome'],
            },
        ),
        migrations.CreateModel(
            name='ShippingRegion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(help_text='Ex: "Capital SP", "Interior", "Norte/Nordeste"', max_length=100, verbose_name='Nome da Região')),
                ('cep_inicio', models.CharField(help_text='Faixa de CEP de destino (apenas números). Ex: 01000000', max_length=8, verbose_name='CEP Início')),
                ('cep_fim', models.CharField(help_text='Ex: 09999999. Deixe vazio para ir até o fim da faixa.', max_length=8, verbose_name='CEP Fim')),
                ('fator', models.DecimalField(decimal_places=2, default=1.0, help_text='Multiplica o valor base da tarifa. Ex: 1.00 (base), 1.20 (+20%).', max_digits=4, verbose_name='Fator de acréscimo')),
                ('ativo', models.BooleanField(default=True, verbose_name='Ativo')),
            ],
            options={
                'verbose_name': 'Região de Entrega',
                'verbose_name_plural': 'Regiões de Entrega',
                'ordering': ['cep_inicio'],
            },
        ),
    ]
