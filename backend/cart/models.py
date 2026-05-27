from django.db import models
from django.conf import settings
from catalog.models import Product


class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='cart', verbose_name='Usuário'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Carrinho'
        verbose_name_plural = 'Carrinhos'

    def __str__(self):
        return f'Carrinho de {self.user.username}'

    @property
    def total(self):
        return sum(item.total for item in self.items.all())

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE, related_name='items',
        verbose_name='Carrinho'
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, verbose_name='Produto'
    )
    quantity = models.PositiveIntegerField('Quantidade', default=1)

    class Meta:
        verbose_name = 'Item do Carrinho'
        verbose_name_plural = 'Itens do Carrinho'
        unique_together = [['cart', 'product']]

    def __str__(self):
        return f'{self.quantity}x {self.product.name}'

    @property
    def total(self):
        return self.product.effective_price * self.quantity
