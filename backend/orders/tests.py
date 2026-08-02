from decimal import Decimal
from io import BytesIO
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from catalog.models import Category, Product
from .models import Order, OrderItem
from .forms import OrderCreateForm


def get_test_image():
    from PIL import Image
    img = Image.new('RGB', (100, 100), color='red')
    buf = BytesIO()
    img.save(buf, 'JPEG')
    return SimpleUploadedFile('test.jpg', buf.getvalue(), content_type='image/jpeg')


class OrderCreateFormTest(TestCase):
    def test_zip_code_comes_before_address(self):
        form = OrderCreateForm()
        fields = list(form.fields.keys())
        self.assertEqual(fields.index('zip_code'), fields.index('phone') + 1)
        self.assertLess(fields.index('zip_code'), fields.index('address'))
        self.assertEqual(fields, ['full_name', 'email', 'phone', 'zip_code', 'address', 'city', 'state'])


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

    def test_order_allows_anonymous_user(self):
        order = Order.objects.create(
            user=None,
            full_name='Cliente Anônimo',
            email='anon@email.com',
            phone='11999999999',
            address='Rua A, 123',
            city='São Paulo',
            state='SP',
            zip_code='01001-001',
        )
        self.assertIsNone(order.user)


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


class OrderDetailViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='teste', password='123')
        self.order = Order.objects.create(
            user=self.user, full_name='João', email='joao@email.com',
            phone='11999999999', address='Rua A', city='SP',
            state='SP', zip_code='01001-001',
        )

    def test_order_detail_requires_login(self):
        response = self.client.get(f'/orders/{self.order.id}/')
        self.assertEqual(response.status_code, 302)

    def test_order_detail_redirects_to_sales_login_when_anonymous(self):
        response = self.client.get(f'/orders/{self.order.id}/')
        self.assertRedirects(response, f'/vendas/entrar/?next=/orders/{self.order.id}/')

    def test_order_detail_shows_correct_order(self):
        self.client.login(username='teste', password='123')
        response = self.client.get(f'/orders/{self.order.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'orders/order_detail.html')

    def test_order_detail_other_user_returns_404(self):
        other = User.objects.create_user(username='outro', password='123')
        other_order = Order.objects.create(
            user=other, full_name='Outro', email='outro@email.com',
            phone='11999999999', address='Rua B', city='SP',
            state='SP', zip_code='01001-001',
        )
        self.client.login(username='teste', password='123')
        response = self.client.get(f'/orders/{other_order.id}/')
        self.assertEqual(response.status_code, 404)
