import json
from decimal import Decimal
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.contrib.auth.models import User

from catalog.models import Category, Product, Variant
from cart.models import Cart, CartItem

MOBILE_UA = (
    'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36'
)
DESKTOP_UA = (
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/120.0 Safari/537.36'
)


def get_test_image():
    from PIL import Image
    img = Image.new('RGB', (100, 100), color='red')
    buf = BytesIO()
    img.save(buf, 'JPEG')
    return SimpleUploadedFile('test.jpg', buf.getvalue(), content_type='image/jpeg')


class MobileTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.client.defaults['HTTP_USER_AGENT'] = MOBILE_UA


class MobileStorePageTest(MobileTestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name='Camisas', slug='camisas',
        )
        self.product = Product.objects.create(
            category=self.category,
            name='Camisa Básica',
            slug='camisa-basica',
            description='Camisa básica preta',
            price=Decimal('99.90'),
            stock=10,
            available=True,
            image=get_test_image(),
        )

    def test_home_returns_200(self):
        response = self.client.get('/m/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Camisa Básica')

    def test_categories_returns_200_with_count(self):
        response = self.client.get('/m/categorias/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Camisas')
        self.assertContains(response, '1 produto')

    def test_products_page_returns_200(self):
        response = self.client.get('/m/produtos/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Camisa Básica')

    def test_products_search_filters_by_name(self):
        response = self.client.get('/m/produtos/?q=Camisa')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Camisa Básica')

    def test_products_search_no_results(self):
        response = self.client.get('/m/produtos/?q=Inexistente')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Camisa Básica')

    def test_category_page_returns_200(self):
        response = self.client.get('/m/categorias/camisas/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Camisa Básica')

    def test_product_detail_returns_200(self):
        response = self.client.get('/m/produto/camisa-basica/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'M2-00001')

    def test_empty_cart_page_returns_200(self):
        response = self.client.get('/m/carrinho/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Seu carrinho está vazio')

    def test_cart_page_with_item(self):
        self.client.post(
            '/carrinho/adicionar/',
            data=json.dumps({'product_id': self.product.id, 'quantity': 2}),
            content_type='application/json',
        )
        response = self.client.get('/m/carrinho/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Camisa Básica')
        self.assertContains(response, 'R$ 199,80')

    def test_checkout_redirects_when_cart_empty(self):
        response = self.client.get('/m/checkout/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/m/carrinho/')


class MobileSalesPageTest(MobileTestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Camisas', slug='camisas')
        self.product = Product.objects.create(
            category=self.category,
            name='Camisa Teste',
            slug='camisa-teste',
            description='Descrição',
            price=Decimal('50.00'),
            stock=5,
            available=True,
            image=get_test_image(),
        )
        self.user = User.objects.create_user(username='vendedor', password='senha123')

    def test_sales_page_requires_login(self):
        response = self.client.get('/m/vendas/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/m/vendas/entrar/', response.url)

    def test_sales_page_renders_for_logged_user(self):
        self.client.login(username='vendedor', password='senha123')
        Cart.objects.create(user=self.user)
        response = self.client.get('/m/vendas/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Venda no Balcão')

    def test_sales_login_page_returns_200(self):
        response = self.client.get('/m/vendas/entrar/')
        self.assertEqual(response.status_code, 200)

    def test_sales_login_redirects_authenticated_user(self):
        self.client.login(username='vendedor', password='senha123')
        response = self.client.get('/m/vendas/entrar/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/m/vendas/')


class MobileProfilePageTest(MobileTestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='cliente', password='senha123')

    def test_anonymous_profile_returns_200(self):
        response = self.client.get('/m/perfil/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Área do Vendedor')

    def test_authenticated_profile_returns_200(self):
        self.client.login(username='cliente', password='senha123')
        response = self.client.get('/m/perfil/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Vendas no Balcão')


class DeviceRedirectTest(MobileTestCase):
    def test_mobile_user_redirected_from_home(self):
        response = self.client.get('/')
        self.assertRedirects(response, '/m/', fetch_redirect_response=False)

    def test_mobile_user_redirected_from_products(self):
        response = self.client.get('/produtos/')
        self.assertRedirects(response, '/m/produtos/', fetch_redirect_response=False)

    def test_mobile_user_redirected_from_category(self):
        response = self.client.get('/produtos/camisas/')
        self.assertRedirects(response, '/m/categorias/camisas/', fetch_redirect_response=False)

    def test_mobile_user_redirected_from_product(self):
        response = self.client.get('/produto/camisa-basica/')
        self.assertRedirects(response, '/m/produto/camisa-basica/', fetch_redirect_response=False)

    def test_mobile_user_redirected_from_cart(self):
        response = self.client.get('/carrinho/')
        self.assertRedirects(response, '/m/carrinho/', fetch_redirect_response=False)

    def test_mobile_user_redirected_from_checkout_success(self):
        response = self.client.get('/checkout/sucesso/1/')
        self.assertRedirects(response, '/m/checkout/sucesso/1/', fetch_redirect_response=False)

    def test_mobile_user_redirected_from_sales_page(self):
        response = self.client.get('/vendas/')
        self.assertRedirects(response, '/m/vendas/', fetch_redirect_response=False)

    def test_mobile_user_redirected_from_sales_login(self):
        response = self.client.get('/vendas/entrar/')
        self.assertRedirects(response, '/m/vendas/entrar/', fetch_redirect_response=False)

    def test_query_string_is_preserved(self):
        response = self.client.get('/produtos/?q=camisa')
        self.assertRedirects(response, '/m/produtos/?q=camisa', fetch_redirect_response=False)

    def test_mobile_user_not_redirected_on_admin(self):
        response = self.client.get('/admin/')
        self.assertFalse(response.headers.get('Location', '').startswith('/m/'))

    def test_mobile_user_not_redirected_on_gerencial(self):
        response = self.client.get('/gerencial/')
        self.assertFalse(response.headers.get('Location', '').startswith('/m/'))

    def test_mobile_user_not_redirected_on_json_api(self):
        response = self.client.get('/buscar/?q=camisa')
        self.assertEqual(response.status_code, 200)

    def test_mobile_user_not_redirected_on_sales_api(self):
        response = self.client.get('/vendas/estoque/?q=x')
        self.assertFalse(response.headers.get('Location', '').startswith('/m/'))

    def test_mobile_user_not_redirected_on_xhr(self):
        response = self.client.get('/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_mobile_user_not_redirected_on_post(self):
        response = self.client.post('/newsletter/', {'email': 'a@b.com'})
        self.assertFalse(response.headers.get('Location', '').startswith('/m/'))

    def test_desktop_user_redirected_from_mobile_home(self):
        response = self.client.get('/m/', HTTP_USER_AGENT=DESKTOP_UA)
        self.assertRedirects(response, '/', fetch_redirect_response=False)

    def test_desktop_user_redirected_from_mobile_category(self):
        response = self.client.get('/m/categorias/camisas/', HTTP_USER_AGENT=DESKTOP_UA)
        self.assertRedirects(response, '/produtos/camisas/', fetch_redirect_response=False)

    def test_desktop_user_redirected_from_mobile_products(self):
        response = self.client.get('/m/produtos/', HTTP_USER_AGENT=DESKTOP_UA)
        self.assertRedirects(response, '/produtos/', fetch_redirect_response=False)

    def test_desktop_user_redirected_from_mobile_product(self):
        response = self.client.get('/m/produto/camisa-basica/', HTTP_USER_AGENT=DESKTOP_UA)
        self.assertRedirects(response, '/produto/camisa-basica/', fetch_redirect_response=False)

    def test_desktop_user_redirected_from_mobile_cart(self):
        response = self.client.get('/m/carrinho/', HTTP_USER_AGENT=DESKTOP_UA)
        self.assertRedirects(response, '/carrinho/', fetch_redirect_response=False)

    def test_desktop_user_redirected_from_mobile_checkout(self):
        response = self.client.get('/m/checkout/', HTTP_USER_AGENT=DESKTOP_UA)
        self.assertRedirects(response, '/checkout/', fetch_redirect_response=False)

    def test_desktop_user_redirected_from_mobile_sales(self):
        response = self.client.get('/m/vendas/', HTTP_USER_AGENT=DESKTOP_UA)
        self.assertRedirects(response, '/vendas/', fetch_redirect_response=False)

    def test_desktop_user_not_redirected_from_mobile_profile(self):
        response = self.client.get('/m/perfil/', HTTP_USER_AGENT=DESKTOP_UA)
        self.assertEqual(response.status_code, 200)

    def test_bot_not_redirected(self):
        response = self.client.get('/', HTTP_USER_AGENT='Googlebot/2.1 (+http://www.google.com/bot.html)')
        self.assertEqual(response.status_code, 200)

    def test_view_mode_mobile_keeps_mobile_for_desktop(self):
        self.client.cookies['view_mode'] = 'mobile'
        response = self.client.get('/m/', HTTP_USER_AGENT=DESKTOP_UA)
        self.assertEqual(response.status_code, 200)

    def test_view_mode_mobile_redirects_desktop_paths(self):
        self.client.cookies['view_mode'] = 'mobile'
        response = self.client.get('/', HTTP_USER_AGENT=DESKTOP_UA)
        self.assertRedirects(response, '/m/', fetch_redirect_response=False)

    def test_view_mode_desktop_keeps_desktop_for_mobile(self):
        self.client.cookies['view_mode'] = 'desktop'
        response = self.client.get('/', HTTP_USER_AGENT=MOBILE_UA)
        self.assertEqual(response.status_code, 200)

    def test_view_mode_desktop_redirects_mobile_paths(self):
        self.client.cookies['view_mode'] = 'desktop'
        response = self.client.get('/m/', HTTP_USER_AGENT=MOBILE_UA)
        self.assertRedirects(response, '/', fetch_redirect_response=False)

    def test_view_mobile_sets_override_cookie(self):
        response = self.client.get('/view/mobile/', HTTP_USER_AGENT=DESKTOP_UA)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.cookies['view_mode'].value, 'mobile')

    def test_view_desktop_sets_override_cookie(self):
        response = self.client.get('/view/desktop/', HTTP_USER_AGENT=MOBILE_UA)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.cookies['view_mode'].value, 'desktop')
