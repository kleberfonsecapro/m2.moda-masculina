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


class CartViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='teste', password='123')
        category = Category.objects.create(name='Camisas', slug='camisas')
        self.product = Product.objects.create(
            category=category, name='Camisa', slug='camisa',
            description='Desc', price=Decimal('100.00'),
            stock=5, available=True, image=get_test_image(),
        )

    def test_cart_requires_login(self):
        response = self.client.get('/cart/')
        self.assertEqual(response.status_code, 302)

    def test_cart_redirects_to_login_when_anonymous(self):
        response = self.client.get('/cart/')
        self.assertRedirects(response, '/accounts/login/?next=/cart/')

    def test_cart_detail_shows_empty_for_logged_user(self):
        self.client.login(username='teste', password='123')
        response = self.client.get('/cart/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cart/cart_detail.html')

    def test_add_to_cart_creates_item(self):
        self.client.login(username='teste', password='123')
        response = self.client.post(f'/cart/adicionar/{self.product.id}/')
        self.assertRedirects(response, '/cart/')
        self.assertEqual(CartItem.objects.count(), 1)

    def test_add_to_cart_increments_existing_item(self):
        self.client.login(username='teste', password='123')
        self.client.post(f'/cart/adicionar/{self.product.id}/')
        self.client.post(f'/cart/adicionar/{self.product.id}/')
        item = CartItem.objects.get(product=self.product)
        self.assertEqual(item.quantity, 2)

    def test_add_unavailable_product_returns_404(self):
        self.client.login(username='teste', password='123')
        self.product.available = False
        self.product.save()
        response = self.client.post(f'/cart/adicionar/{self.product.id}/')
        self.assertEqual(response.status_code, 404)

    def test_add_nonexistent_product_returns_404(self):
        self.client.login(username='teste', password='123')
        response = self.client.post('/cart/adicionar/99999/')
        self.assertEqual(response.status_code, 404)

    def test_remove_item_from_cart(self):
        self.client.login(username='teste', password='123')
        self.client.post(f'/cart/adicionar/{self.product.id}/')
        item = CartItem.objects.get()
        response = self.client.post(f'/cart/remover/{item.id}/')
        self.assertRedirects(response, '/cart/')
        self.assertEqual(CartItem.objects.count(), 0)

    def test_remove_other_users_item_returns_404(self):
        other = User.objects.create_user(username='outro', password='123')
        other_cart = Cart.objects.create(user=other)
        CartItem.objects.create(cart=other_cart, product=self.product)
        self.client.login(username='teste', password='123')
        response = self.client.post('/cart/remover/1/')
        self.assertEqual(response.status_code, 404)

    def test_update_item_quantity(self):
        self.client.login(username='teste', password='123')
        self.client.post(f'/cart/adicionar/{self.product.id}/')
        item = CartItem.objects.get()
        response = self.client.post(f'/cart/atualizar/{item.id}/', {'quantity': 5})
        self.assertRedirects(response, '/cart/')
        item.refresh_from_db()
        self.assertEqual(item.quantity, 5)

    def test_update_item_to_zero_removes_it(self):
        self.client.login(username='teste', password='123')
        self.client.post(f'/cart/adicionar/{self.product.id}/')
        item = CartItem.objects.get()
        self.client.post(f'/cart/atualizar/{item.id}/', {'quantity': 0})
        self.assertEqual(CartItem.objects.count(), 0)

    def test_cart_shows_item_in_detail(self):
        self.client.login(username='teste', password='123')
        self.client.post(f'/cart/adicionar/{self.product.id}/')
        response = self.client.get('/cart/')
        self.assertContains(response, 'Camisa')
