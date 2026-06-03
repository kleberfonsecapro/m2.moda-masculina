from decimal import Decimal
from io import BytesIO
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from catalog.models import Category, Product
from cart.models import Cart, CartItem
from .models import Order, OrderItem


def get_test_image():
    from PIL import Image
    img = Image.new('RGB', (100, 100), color='red')
    buf = BytesIO()
    img.save(buf, 'JPEG')
    return SimpleUploadedFile('test.jpg', buf.getvalue(), content_type='image/jpeg')


class OrderModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='teste', password='123')
        self.order = Order.objects.create(
            user=self.user,
            full_name='João Silva',
            email='joao@email.com',
            phone='11999999999',
            address='Rua A, 123',
            city='São Paulo',
            state='SP',
            zip_code='01001-001',
        )

    def test_order_str(self):
        self.assertIn('Pedido #', str(self.order))
        self.assertIn('teste', str(self.order))

    def test_order_default_status_is_pending(self):
        self.assertEqual(self.order.status, 'pending')

    def test_order_total_without_items(self):
        self.assertEqual(self.order.total, 0)

    def test_order_total_with_items(self):
        category = Category.objects.create(name='Camisas', slug='camisas')
        product = Product.objects.create(
            category=category, name='Camisa', slug='camisa',
            description='Desc', price=Decimal('100.00'), stock=5,
            image=get_test_image(),
        )
        OrderItem.objects.create(
            order=self.order, product=product,
            price=Decimal('100.00'), quantity=2,
        )
        self.assertEqual(self.order.total, Decimal('200.00'))


class OrderItemModelTest(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='teste', password='123')
        order = Order.objects.create(
            user=user, full_name='João', email='joao@email.com',
            phone='11999999999', address='Rua A', city='SP',
            state='SP', zip_code='01001-001',
        )
        category = Category.objects.create(name='Camisas', slug='camisas')
        product = Product.objects.create(
            category=category, name='Camisa', slug='camisa',
            description='Desc', price=Decimal('100.00'), stock=5,
            image=get_test_image(),
        )
        self.item = OrderItem.objects.create(
            order=order, product=product,
            price=Decimal('100.00'), quantity=3,
        )

    def test_order_item_str(self):
        self.assertEqual(str(self.item), '3x Camisa')

    def test_order_item_total(self):
        self.assertEqual(self.item.total, Decimal('300.00'))


class OrderFlowTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='teste', password='123')
        category = Category.objects.create(name='Camisas', slug='camisas')
        self.product = Product.objects.create(
            category=category, name='Camisa', slug='camisa',
            description='Desc', price=Decimal('100.00'),
            promotional_price=Decimal('79.90'),
            stock=5, available=True, image=get_test_image(),
        )
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)

    def test_order_create_status(self):
        self.client.login(username='teste', password='123')
        response = self.client.get('/orders/criar/')
        self.assertEqual(response.status_code, 200)

    def test_order_create_uses_correct_template(self):
        self.client.login(username='teste', password='123')
        response = self.client.get('/orders/criar/')
        self.assertTemplateUsed(response, 'orders/order_create.html')

    def test_order_create_requires_login(self):
        response = self.client.get('/orders/criar/')
        self.assertEqual(response.status_code, 302)

    def test_create_order_successfully(self):
        self.client.login(username='teste', password='123')
        response = self.client.post('/orders/criar/', {
            'full_name': 'João Silva',
            'email': 'joao@email.com',
            'phone': '11999999999',
            'address': 'Rua A, 123',
            'city': 'São Paulo',
            'state': 'SP',
            'zip_code': '01001-001',
        })
        self.assertRedirects(response, '/orders/1/')
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 1)

    def test_order_uses_promotional_price(self):
        self.client.login(username='teste', password='123')
        self.client.post('/orders/criar/', {
            'full_name': 'João Silva',
            'email': 'joao@email.com',
            'phone': '11999999999',
            'address': 'Rua A, 123',
            'city': 'São Paulo',
            'state': 'SP',
            'zip_code': '01001-001',
        })
        item = OrderItem.objects.get()
        self.assertEqual(item.price, Decimal('79.90'))

    def test_order_empties_cart(self):
        self.client.login(username='teste', password='123')
        self.client.post('/orders/criar/', {
            'full_name': 'João Silva',
            'email': 'joao@email.com',
            'phone': '11999999999',
            'address': 'Rua A, 123',
            'city': 'São Paulo',
            'state': 'SP',
            'zip_code': '01001-001',
        })
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.items.count(), 0)

    def test_create_order_with_empty_cart_redirects(self):
        self.client.login(username='teste', password='123')
        Cart.objects.get(user=self.user).items.all().delete()
        response = self.client.get('/orders/criar/')
        self.assertRedirects(response, '/produtos/')

    def test_order_detail_shows_correct_order(self):
        self.client.login(username='teste', password='123')
        self.client.post('/orders/criar/', {
            'full_name': 'João Silva',
            'email': 'joao@email.com',
            'phone': '11999999999',
            'address': 'Rua A, 123',
            'city': 'São Paulo',
            'state': 'SP',
            'zip_code': '01001-001',
        })
        response = self.client.get('/orders/1/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'orders/order_detail.html')

    def test_order_detail_other_user_returns_404(self):
        other = User.objects.create_user(username='outro', password='123')
        Order.objects.create(
            user=other, full_name='Outro', email='outro@email.com',
            phone='11999999999', address='Rua B', city='SP',
            state='SP', zip_code='01001-001',
        )
        self.client.login(username='teste', password='123')
        response = self.client.get('/orders/1/')
        self.assertEqual(response.status_code, 404)

    def test_order_list_shows_user_orders(self):
        self.client.login(username='teste', password='123')
        Order.objects.create(
            user=self.user, full_name='João', email='joao@email.com',
            phone='11999999999', address='Rua A', city='SP',
            state='SP', zip_code='01001-001',
        )
        response = self.client.get('/orders/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'orders/order_list.html')
