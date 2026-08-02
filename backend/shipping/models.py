from django.db import models


class ShippingConfig(models.Model):
    cep_origem = models.CharField('CEP de Origem', max_length=8,
        help_text='CEP de onde os pedidos são enviados (apenas números)')
    peso_padrao_kg = models.DecimalField(
        'Peso padrão da embalagem (kg)', max_digits=5, decimal_places=2, default=1.00,
        help_text='Peso médio da caixa com os produtos. O cálculo usa peso real OU cúbico, o que for maior.'
    )
    comprimento_cm = models.DecimalField(
        'Comprimento da embalagem (cm)', max_digits=6, decimal_places=2, default=30
    )
    largura_cm = models.DecimalField(
        'Largura da embalagem (cm)', max_digits=6, decimal_places=2, default=20
    )
    altura_cm = models.DecimalField(
        'Altura da embalagem (cm)', max_digits=6, decimal_places=2, default=10
    )
    frete_gratis_acima_de = models.DecimalField(
        'Frete grátis acima de (R$)', max_digits=10, decimal_places=2,
        blank=True, null=True,
        help_text='Se o subtotal do pedido for maior ou igual a este valor, o frete fica grátis. Deixe vazio para nunca dar frete grátis.'
    )
    ativo = models.BooleanField('Ativo', default=True,
        help_text='Quando desativado, o cálculo de frete fica indisponível no site.')

    class Meta:
        verbose_name = 'Configuração de Frete'
        verbose_name_plural = 'Configurações de Frete'

    def __str__(self):
        return f'Frete - origem {self.cep_origem}'

    def save(self, *args, **kwargs):
        if not self.pk and ShippingConfig.objects.exists():
            return
        super().save(*args, **kwargs)


class ShippingRegion(models.Model):
    nome = models.CharField('Nome da Região', max_length=100,
        help_text='Ex: "Capital SP", "Interior", "Norte/Nordeste"')
    cep_inicio = models.CharField('CEP Início', max_length=8,
        help_text='Faixa de CEP de destino (apenas números). Ex: 01000000')
    cep_fim = models.CharField('CEP Fim', max_length=8,
        help_text='Ex: 09999999. Deixe vazio para ir até o fim da faixa.')
    fator = models.DecimalField(
        'Fator de acréscimo', max_digits=4, decimal_places=2, default=1.00,
        help_text='Multiplica o valor base da tarifa. Ex: 1.00 (base), 1.20 (+20%).'
    )
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Região de Entrega'
        verbose_name_plural = 'Regiões de Entrega'
        ordering = ['cep_inicio']

    def __str__(self):
        return f'{self.nome} ({self.cep_inicio}-{self.cep_fim})'


class ShippingRate(models.Model):
    nome = models.CharField('Serviço de Envio', max_length=100,
        help_text='Ex: "Sedex", "PAC", "Retirada na loja"')
    peso_min_kg = models.DecimalField('Peso mínimo (kg)', max_digits=5, decimal_places=2, default=0)
    peso_max_kg = models.DecimalField('Peso máximo (kg)', max_digits=5, decimal_places=2, default=1)
    valor_base = models.DecimalField('Valor base (R$)', max_digits=10, decimal_places=2,
        help_text='Tarifa para esta faixa de peso. Será multiplicada pelo fator da região do CEP de destino.')
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Tarifa de Envio'
        verbose_name_plural = 'Tarifas de Envio'
        ordering = ['peso_min_kg', 'nome']

    def __str__(self):
        return f'{self.nome} ({self.peso_min_kg}kg-{self.peso_max_kg}kg) - R$ {self.valor_base}'
