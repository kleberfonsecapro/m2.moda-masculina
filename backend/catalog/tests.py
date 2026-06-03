from decimal import Decimal
from io import BytesIO
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Category, Product, SiteConfig, CarouselSettings


def get_test_image():
    from PIL import Image
    img = Image.new('RGB', (100, 100), color='red')
    buf = BytesIO()
    img.save(buf, 'JPEG')
    return SimpleUploadedFile('test.jpg', buf.getvalue(), content_type='image/jpeg')


class CategoryModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name='Camisas Peruanas',
            slug='camisas-peruanas',
            description='Camisas peruanas artesanais',
        )

    def test_category_str(self):
        self.assertEqual(str(self.category), 'Camisas Peruanas')

    def test_category_get_absolute_url(self):
        url = self.category.get_absolute_url()
        self.assertEqual(url, '/produtos/camisas-peruanas/')

    def test_category_featured_defaults_to_false(self):
        self.assertFalse(self.category.featured)


class ProductModelTest(TestCase):
    def setUp(self):
        category = Category.objects.create(name='Camisas', slug='camisas')
        self.product = Product.objects.create(
            category=category,
            name='Camisa Teste',
            slug='camisa-teste',
            description='Descrição da camisa',
            price=Decimal('100.00'),
            stock=10,
            available=True,
            image=get_test_image(),
        )

    def test_product_str(self):
        self.assertEqual(str(self.product), 'M2-00001 - Camisa Teste')

    def test_product_code_auto_generated(self):
        self.assertEqual(self.product.code, 'M2-00001')

    def test_product_code_is_unique(self):
        with self.assertRaises(Exception):
            Product.objects.create(
                category=self.product.category, name='Outra', slug='outra',
                description='Desc', price=Decimal('50.00'), stock=5,
                image=get_test_image(), code='M2-00001',
            )

    def test_product_qrcode_generated_on_save(self):
        self.assertTrue(self.product.qrcode_image)
        self.assertTrue(self.product.qrcode_image.name.startswith('qrcodes/qrcode_M2-'))

    def test_effective_price_without_promotion(self):
        self.assertEqual(self.product.effective_price, Decimal('100.00'))

    def test_effective_price_with_promotion(self):
        self.product.promotional_price = Decimal('79.90')
        self.assertEqual(self.product.effective_price, Decimal('79.90'))

    def test_effective_price_returns_decimal(self):
        self.assertIsInstance(self.product.effective_price, Decimal)

    def test_stock_value_uses_purchase_price(self):
        self.product.purchase_price = Decimal('50.00')
        self.product.stock = 10
        self.assertEqual(self.product.stock_value, Decimal('500.00'))

    def test_stock_value_defaults_to_zero(self):
        self.product.purchase_price = Decimal('0')
        self.product.stock = 5
        self.assertEqual(self.product.stock_value, Decimal('0'))

    def test_purchase_price_defaults_to_zero(self):
        self.assertEqual(self.product.purchase_price, Decimal('0'))

    def test_product_available_defaults_to_true(self):
        self.assertTrue(self.product.available)

    def test_product_featured_defaults_to_false(self):
        self.assertFalse(self.product.featured)

    def test_product_get_absolute_url(self):
        url = self.product.get_absolute_url()
        self.assertEqual(url, '/produto/camisa-teste/')


class HomeViewTest(TestCase):
    def setUp(self):
        category = Category.objects.create(name='Camisas', slug='camisas')
        Product.objects.create(
            category=category, name='Camisa', slug='camisa',
            description='Desc', price=Decimal('100.00'),
            stock=5, available=True, image=get_test_image(),
        )

    def test_home_status(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_home_uses_correct_template(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'catalog/home.html')

    def test_home_contains_product(self):
        response = self.client.get('/')
        self.assertContains(response, 'Camisa')


class ProductListViewTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Camisas', slug='camisas')
        Category.objects.create(name='Calcados', slug='calcados')
        Product.objects.create(
            category=self.category, name='Camisa A', slug='camisa-a',
            description='Desc', price=Decimal('100.00'),
            stock=5, available=True, image=get_test_image(),
        )
        Product.objects.create(
            category=self.category, name='Camisa B', slug='camisa-b',
            description='Desc', price=Decimal('150.00'),
            stock=3, available=False, image=get_test_image(),
        )

    def test_product_list_status(self):
        response = self.client.get('/produtos/')
        self.assertEqual(response.status_code, 200)

    def test_product_list_shows_only_available(self):
        response = self.client.get('/produtos/')
        self.assertContains(response, 'Camisa A')
        self.assertNotContains(response, 'Camisa B')

    def test_product_list_filter_by_category(self):
        response = self.client.get('/produtos/camisas/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Camisa A')

    def test_product_list_invalid_category_returns_404(self):
        response = self.client.get('/produtos/nao-existe/')
        self.assertEqual(response.status_code, 404)

    def test_product_list_uses_correct_template(self):
        response = self.client.get('/produtos/')
        self.assertTemplateUsed(response, 'catalog/product_list.html')


class ProductDetailViewTest(TestCase):
    def setUp(self):
        category = Category.objects.create(name='Camisas', slug='camisas')
        self.product = Product.objects.create(
            category=category, name='Camisa Teste', slug='camisa-teste',
            description='Descrição detalhada', price=Decimal('100.00'),
            stock=5, available=True, image=get_test_image(),
        )

    def test_product_detail_status(self):
        response = self.client.get('/produto/camisa-teste/')
        self.assertEqual(response.status_code, 200)

    def test_product_detail_contains_name(self):
        response = self.client.get('/produto/camisa-teste/')
        self.assertContains(response, 'Camisa Teste')

    def test_product_detail_contains_description(self):
        response = self.client.get('/produto/camisa-teste/')
        self.assertContains(response, 'Descrição detalhada')

    def test_product_detail_not_found(self):
        response = self.client.get('/produto/nao-existe/')
        self.assertEqual(response.status_code, 404)

    def test_product_detail_unavailable_returns_404(self):
        self.product.available = False
        self.product.save()
        response = self.client.get('/produto/camisa-teste/')
        self.assertEqual(response.status_code, 404)

    def test_product_detail_uses_correct_template(self):
        response = self.client.get('/produto/camisa-teste/')
        self.assertTemplateUsed(response, 'catalog/product_detail.html')

    def test_product_detail_shows_related_products(self):
        other = Product.objects.create(
            category=self.product.category, name='Outra Camisa',
            slug='outra-camisa', description='Outra',
            price=Decimal('80.00'), stock=2, available=True,
            image=get_test_image(),
        )
        response = self.client.get('/produto/camisa-teste/')
        self.assertContains(response, 'Outra Camisa')

    def test_product_detail_excludes_self_from_related(self):
        response = self.client.get('/produto/camisa-teste/')
        self.assertEqual(len(response.context['related_products']), 0)


class SiteConfigTest(TestCase):
    def test_site_config_is_singleton(self):
        SiteConfig.objects.create(whatsapp_number='5511999999999')
        SiteConfig.objects.create(whatsapp_number='5511888888888')
        self.assertEqual(SiteConfig.objects.count(), 1)

    def test_site_config_str(self):
        config = SiteConfig.objects.create(whatsapp_number='5511999999999')
        self.assertEqual(str(config), 'Configurações do Site')


class CarouselSettingsTest(TestCase):
    def test_carousel_settings_is_singleton(self):
        CarouselSettings.objects.create(autoplay_interval=3000)
        CarouselSettings.objects.create(autoplay_interval=5000)
        self.assertEqual(CarouselSettings.objects.count(), 1)

    def test_carousel_settings_defaults(self):
        settings = CarouselSettings.objects.create()
        self.assertEqual(settings.autoplay_interval, 5000)
        self.assertEqual(settings.transition_speed, 800)


class SalesPageTest(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username='vendedor', password='123')
        self.category = Category.objects.create(name='Roupas', slug='roupas')
        self.product = Product.objects.create(
            category=self.category, name='Camisa', slug='camisa',
            description='Desc', price=Decimal('89.90'),
            stock=10, available=True, image=get_test_image(),
        )

    def test_sales_page_redirects_anonymous(self):
        response = self.client.get('/vendas/')
        self.assertEqual(response.status_code, 302)

    def test_sales_page_loads_for_logged_user(self):
        self.client.login(username='vendedor', password='123')
        response = self.client.get('/vendas/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/sales.html')

    def test_sales_product_lookup_by_code(self):
        self.client.login(username='vendedor', password='123')
        response = self.client.get(f'/vendas/buscar/?code={self.product.code}')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['name'], 'Camisa')

    def test_sales_product_lookup_invalid_code(self):
        self.client.login(username='vendedor', password='123')
        response = self.client.get('/vendas/buscar/?code=INVALIDO')
        self.assertEqual(response.status_code, 404)

    def test_sales_add_item_to_cart(self):
        self.client.login(username='vendedor', password='123')
        response = self.client.post(
            '/vendas/adicionar/',
            {'code': self.product.code, 'quantity': 2},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['product']['name'], 'Camisa')

    def test_sales_add_item_exceeds_stock(self):
        self.client.login(username='vendedor', password='123')
        self.product.stock = 3
        self.product.save()
        response = self.client.post(
            '/vendas/adicionar/',
            {'code': self.product.code, 'quantity': 5},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('Estoque insuficiente', response.json()['error'])

    def test_sales_add_item_requires_auth(self):
        response = self.client.post(
            '/vendas/adicionar/',
            {'code': self.product.code},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 302)

    def test_sales_checkout_creates_order_and_reduces_stock(self):
        self.client.login(username='vendedor', password='123')
        self.product.stock = 10
        self.product.save()
        self.client.post(
            '/vendas/adicionar/',
            {'code': self.product.code, 'quantity': 3},
            content_type='application/json',
        )
        response = self.client.post(
            '/vendas/finalizar/',
            {'payment_method': 'pix', 'customer_name': 'João', 'customer_phone': '11999999999'},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('redirect', data)
        self.assertEqual(data['payment_method'], 'PIX')

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 7)

    def test_sales_checkout_with_invalid_payment(self):
        self.client.login(username='vendedor', password='123')
        self.client.post(
            '/vendas/adicionar/',
            {'code': self.product.code, 'quantity': 1},
            content_type='application/json',
        )
        response = self.client.post(
            '/vendas/finalizar/',
            {'payment_method': 'invalid'},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_sales_checkout_empty_cart(self):
        self.client.login(username='vendedor', password='123')
        response = self.client.post(
            '/vendas/finalizar/',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
