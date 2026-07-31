from django.db import models
from django.conf import settings
from catalog.models import Product, Variant


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('confirmed', 'Confirmado'),
        ('processing', 'Em Preparação'),
        ('shipped', 'Enviado'),
        ('delivered', 'Entregue'),
        ('cancelled', 'Cancelado'),
    ]

    PAYMENT_CHOICES = [
        ('cash', 'Dinheiro'),
        ('card', 'Cartão'),
        ('pix', 'PIX'),
        ('other', 'Outro'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='orders', verbose_name='Usuário',
        blank=True, null=True
    )
    full_name = models.CharField('Nome Completo', max_length=100)
    email = models.EmailField('E-mail')
    phone = models.CharField('Telefone', max_length=20)
    address = models.CharField('Endereço', max_length=255)
    city = models.CharField('Cidade', max_length=100)
    state = models.CharField('Estado', max_length=50)
    zip_code = models.CharField('CEP', max_length=10)
    payment_method = models.CharField(
        'Forma de Pagamento', max_length=20, choices=PAYMENT_CHOICES, default='cash'
    )
    status = models.CharField(
        'Status', max_length=20, choices=STATUS_CHOICES, default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-created_at']

    def __str__(self):
        return f'Pedido #{self.id} - {self.user.username}'

    @property
    def total(self):
        return sum(item.total for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='items',
        verbose_name='Pedido'
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, verbose_name='Produto'
    )
    variant = models.ForeignKey(
        Variant, on_delete=models.CASCADE, verbose_name='Variação',
        blank=True, null=True
    )
    price = models.DecimalField('Preço', max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField('Quantidade', default=1)

    class Meta:
        verbose_name = 'Item do Pedido'
        verbose_name_plural = 'Itens do Pedido'

    def __str__(self):
        label = f'{self.product.name}'
        if self.variant:
            label += f' ({self.variant})'
        return f'{self.quantity}x {label}'

    @property
    def total(self):
        return self.price * self.quantity
