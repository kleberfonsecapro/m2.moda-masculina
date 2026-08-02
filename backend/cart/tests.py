from decimal import Decimal
from io import BytesIO
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from catalog.models import Category, Product, Variant
from .models import Cart, CartItem


def get_test_image():
    from PIL import Image
    img = Image.new('RGB', (100, 100), color='red')
    buf = BytesIO()
    img.save(buf, 'JPEG')
    return SimpleUploadedFile('test.jpg', buf.getvalue(), content_type='image/jpeg')


class CartModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='teste', password='123')
        self.cart = Cart.objects.create(user=self.user)
        category = Category.objects.create(name='Camisas', slug='camisas')
        self.product = Product.objects.create(
            category=category, name='Camisa', slug='camisa',
            description='Desc', price=Decimal('100.00'),
            stock=5, available=True, image=get_test_image(),
        )

    def test_cart_str(self):
        self.assertEqual(str(self.cart), 'Carrinho de teste')

    def test_empty_cart_total(self):
        self.assertEqual(self.cart.total, 0)

    def test_empty_cart_total_items(self):
        self.assertEqual(self.cart.total_items, 0)

    def test_cart_total_with_items(self):
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)
        self.assertEqual(self.cart.total, Decimal('200.00'))

    def test_cart_total_items_count(self):
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=3)
        self.assertEqual(self.cart.total_items, 3)


class CartItemModelTest(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='teste', password='123')
        cart = Cart.objects.create(user=user)
        category = Category.objects.create(name='Camisas', slug='camisas')
        self.product = Product.objects.create(
            category=category, name='Camisa', slug='camisa',
            description='Desc', price=Decimal('100.00'),
            stock=5, available=True, image=get_test_image(),
        )
        self.variant = Variant.objects.create(
            product=self.product, size='M', stock=3
        )
        self.item = CartItem.objects.create(cart=cart, product=self.product, quantity=2)

    def test_cart_item_str(self):
        self.assertEqual(str(self.item), '2x Camisa')

    def test_cart_item_total(self):
        self.assertEqual(self.item.total, Decimal('200.00'))

    def test_cart_item_total_with_promotion(self):
        self.product.promotional_price = Decimal('79.90')
        self.assertEqual(self.item.total, Decimal('159.80'))

    def test_unique_with_variant_constraint(self):
        with self.assertRaises(Exception):
            CartItem.objects.create(
                cart=self.item.cart, product=self.product,
                variant=self.variant, quantity=1,
            )
            CartItem.objects.create(
                cart=self.item.cart, product=self.product,
                variant=self.variant, quantity=1,
            )
