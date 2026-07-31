from decimal import Decimal
from io import BytesIO
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Category, Product, Variant, Newsletter, SiteConfig, CarouselSettings, TickerMessage


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


class VariantModelTest(TestCase):
    def setUp(self):
        category = Category.objects.create(name='Camisas', slug='camisas')
        self.product = Product.objects.create(
            category=category, name='Camisa', slug='camisa',
            description='Desc', price=Decimal('100.00'),
            stock=10, available=True, image=get_test_image(),
        )
        self.variant = Variant.objects.create(
            product=self.product, size='M', color='Preto',
            stock=3, sku='CAM-M-PT', order=1,
        )

    def test_variant_str_with_size_and_color(self):
        expected = 'Camisa - M / Preto'
        self.assertEqual(str(self.variant), expected)

    def test_variant_str_size_only(self):
        v = Variant.objects.create(product=self.product, size='G', stock=2)
        self.assertEqual(str(v), 'Camisa - G')

    def test_variant_unique_together(self):
        with self.assertRaises(Exception):
            Variant.objects.create(
                product=self.product, size='M', color='Preto', stock=1,
            )

    def test_variant_default_stock(self):
        v = Variant.objects.create(product=self.product, size='P')
        self.assertEqual(v.stock, 0)

    def test_variant_default_order(self):
        v = Variant.objects.create(product=self.product, size='P')
        self.assertEqual(v.order, 0)


class NewsletterModelTest(TestCase):
    def test_newsletter_creation(self):
        nl = Newsletter.objects.create(email='teste@teste.com')
        self.assertEqual(str(nl), 'teste@teste.com')

    def test_newsletter_unique_email(self):
        Newsletter.objects.create(email='teste@teste.com')
        with self.assertRaises(Exception):
            Newsletter.objects.create(email='teste@teste.com')


class ProductPropertiesTest(TestCase):
    def setUp(self):
        category = Category.objects.create(name='Camisas', slug='camisas')
        self.product = Product.objects.create(
            category=category, name='Camisa', slug='camisa',
            description='Desc', price=Decimal('100.00'),
            promotional_price=Decimal('69.90'), stock=10,
            available=True, image=get_test_image(),
        )

    def test_discount_percentage(self):
        self.assertEqual(self.product.discount_percentage, 30)

    def test_discount_percentage_zero_when_no_promotion(self):
        self.product.promotional_price = None
        self.assertEqual(self.product.discount_percentage, 0)

    def test_has_variants_false_initially(self):
        self.assertFalse(self.product.has_variants)

    def test_has_variants_true_with_variants(self):
        Variant.objects.create(product=self.product, size='M', stock=3)
        self.assertTrue(self.product.has_variants)

    def test_sorted_sizes(self):
        for size in ['GG', 'P', 'M', 'G']:
            Variant.objects.create(product=self.product, size=size, stock=1)
        sizes = [v.size for v in self.product.sorted_sizes]
        self.assertEqual(sizes, ['P', 'M', 'G', 'GG'])


class ProductSearchViewTest(TestCase):
    def setUp(self):
        category = Category.objects.create(name='Camisas', slug='camisas')
        self.product = Product.objects.create(
            category=category, name='Camisa Polo', slug='camisa-polo',
            description='Desc', price=Decimal('100.00'),
            stock=5, available=True, image=get_test_image(),
        )
        Product.objects.create(
            category=category, name='Camiseta', slug='camiseta',
            description='Desc', price=Decimal('50.00'),
            stock=3, available=True, image=get_test_image(),
        )

    def test_search_by_name(self):
        response = self.client.get('/buscar/?q=Polo')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['name'], 'Camisa Polo')

    def test_search_returns_empty_for_short_query(self):
        response = self.client.get('/buscar/?q=a')
        data = response.json()
        self.assertEqual(len(data['results']), 0)

    def test_search_returns_all_matches(self):
        response = self.client.get('/buscar/?q=camis')
        data = response.json()
        self.assertEqual(len(data['results']), 2)


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


class TickerMessageTest(TestCase):
    def setUp(self):
        TickerMessage.objects.all().delete()
        self.phrase = TickerMessage.objects.create(text='🔥 Promoção relâmpago', order=1)

    def test_ticker_str(self):
        self.assertEqual(str(self.phrase), '🔥 Promoção relâmpago')

    def test_ticker_ordering(self):
        TickerMessage.objects.create(text='Primeira', order=0)
        texts = list(TickerMessage.objects.values_list('text', flat=True))
        self.assertEqual(texts, ['Primeira', '🔥 Promoção relâmpago'])

    def test_ticker_active_defaults_to_true(self):
        self.assertTrue(self.phrase.active)


class TickerContextProcessorTest(TestCase):
    def setUp(self):
        TickerMessage.objects.all().delete()

    def test_returns_default_when_no_messages(self):
        response = self.client.get('/')
        self.assertEqual(response.context['ticker_messages'], ['🔥 Moda masculina com estilo e atitude'])
        self.assertEqual(response.context['ticker_duration'], 16)

    def test_returns_only_active_ordered_messages(self):
        TickerMessage.objects.create(text='Segunda frase', order=1, active=True)
        TickerMessage.objects.create(text='Primeira frase', order=0, active=True)
        TickerMessage.objects.create(text='Inativa', order=2, active=False)
        response = self.client.get('/')
        self.assertEqual(
            response.context['ticker_messages'],
            ['Primeira frase', 'Segunda frase'],
        )

    def test_duration_scales_with_message_count(self):
        for i in range(3):
            TickerMessage.objects.create(text=f'Frase {i}', order=i, active=True)
        response = self.client.get('/')
        self.assertEqual(response.context['ticker_duration'], 24)

    def test_ticker_rendered_on_home(self):
        TickerMessage.objects.create(text='🔥 Moda masculina com estilo e atitude', order=0, active=True)
        response = self.client.get('/')
        self.assertContains(response, 'ticker-track')
        self.assertContains(response, 'Moda masculina com estilo e atitude')


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


class StoreCartTest(TestCase):
    def setUp(self):
        category = Category.objects.create(name='Roupas', slug='roupas')
        self.product = Product.objects.create(
            category=category, name='Camisa Polo', slug='camisa-polo',
            description='Desc', price=Decimal('100.00'),
            stock=10, available=True, image=get_test_image(),
        )

    def post_json(self, url, payload):
        return self.client.post(
            url, payload, content_type='application/json',
        )

    def add(self, product_id, quantity=1, variant_id=None):
        return self.post_json('/carrinho/adicionar/', {
            'product_id': product_id,
            'variant_id': variant_id,
            'quantity': quantity,
        })

    def test_add_to_cart_success(self):
        response = self.add(self.product.id)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['cart_count'], 1)

    def test_add_to_cart_increments_existing_item(self):
        self.add(self.product.id)
        response = self.add(self.product.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['cart_count'], 2)

    def test_add_to_cart_multiple_products(self):
        other = Product.objects.create(
            category=self.product.category, name='Camiseta', slug='camiseta',
            description='Desc', price=Decimal('50.00'),
            stock=5, available=True, image=get_test_image(),
        )
        self.add(self.product.id)
        response = self.add(other.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['cart_count'], 2)

    def test_add_to_cart_exceeds_stock(self):
        self.product.stock = 3
        self.product.save()
        response = self.add(self.product.id, quantity=5)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Estoque insuficiente', response.json()['error'])

    def test_add_to_cart_accumulated_exceeds_stock(self):
        self.product.stock = 2
        self.product.save()
        self.add(self.product.id)
        response = self.add(self.product.id, quantity=2)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Estoque insuficiente', response.json()['error'])

    def test_add_to_cart_invalid_json(self):
        response = self.client.post(
            '/carrinho/adicionar/',
            data='not-json',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_add_to_cart_missing_product(self):
        response = self.post_json('/carrinho/adicionar/', {'quantity': 1})
        self.assertEqual(response.status_code, 400)
        self.assertIn('obrigatórios', response.json()['error'])

    def test_add_to_cart_zero_quantity(self):
        response = self.add(self.product.id, quantity=0)
        self.assertEqual(response.status_code, 400)

    def test_add_to_cart_unavailable_product(self):
        self.product.available = False
        self.product.save()
        response = self.add(self.product.id)
        self.assertEqual(response.status_code, 404)

    def test_add_to_cart_nonexistent_product(self):
        response = self.add(9999)
        self.assertEqual(response.status_code, 404)

    def test_add_to_cart_requires_post(self):
        response = self.client.get('/carrinho/adicionar/')
        self.assertEqual(response.status_code, 405)

    def test_update_cart_increase(self):
        self.add(self.product.id)
        response = self.post_json('/carrinho/atualizar/', {
            'key': f'{self.product.id}-', 'action': 'increase',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['cart_count'], 2)

    def test_update_cart_decrease(self):
        self.add(self.product.id)
        self.add(self.product.id)
        response = self.post_json('/carrinho/atualizar/', {
            'key': f'{self.product.id}-', 'action': 'decrease',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['cart_count'], 1)

    def test_update_cart_decrease_never_below_one(self):
        self.add(self.product.id)
        response = self.post_json('/carrinho/atualizar/', {
            'key': f'{self.product.id}-', 'action': 'decrease',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['cart_count'], 1)

    def test_update_cart_remove(self):
        self.add(self.product.id)
        response = self.post_json('/carrinho/atualizar/', {
            'key': f'{self.product.id}-', 'action': 'remove',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['cart_count'], 0)

    def test_cart_page_empty(self):
        response = self.client.get('/carrinho/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Seu carrinho está vazio')

    def test_cart_page_shows_item(self):
        self.add(self.product.id)
        response = self.client.get('/carrinho/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Camisa Polo')
