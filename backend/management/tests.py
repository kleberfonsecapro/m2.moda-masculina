from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from catalog.models import Category, Product
from orders.models import Order, OrderItem


class ExportOrdersCsvTest(TestCase):
    def setUp(self):
        self.manager = User.objects.create_superuser(
            username='gerente',
            email='gerente@example.com',
            password='senha-de-teste-forte',
        )
        self.client.force_login(self.manager)
        self.order = Order.objects.create(
            full_name='=HYPERLINK("https://evil.example","clique")',
            email='cliente@example.com',
            phone='+55 11 99999-9999',
            cpf='@12345678900',
            address='-Rua A, 123',
            city='São Paulo',
            state='SP',
            zip_code='01001-001',
        )

    def test_export_neutralizes_formula_injection(self):
        response = self.client.get('/gerencial/pedidos/exportar/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')

        body = response.content.decode('utf-8')
        self.assertIn("'=HYPERLINK", body)
        self.assertIn("'+55 11", body)
        self.assertIn("'@12345678900", body)
        self.assertIn("'-Rua A", body)
        # Dados legítimos permanecem intactos.
        self.assertIn('cliente@example.com', body)

    def test_export_applies_list_filters(self):
        Order.objects.create(
            full_name='Outro Cliente',
            email='outro@example.com',
            phone='11999999999',
            address='Rua B',
            city='Rio de Janeiro',
            state='RJ',
            zip_code='20000-000',
            status='cancelled',
        )

        response = self.client.get('/gerencial/pedidos/exportar/', {'status': 'pending'})

        body = response.content.decode('utf-8')
        self.assertIn("'=HYPERLINK", body)
        self.assertNotIn('Outro Cliente', body)

    def test_export_requires_manager(self):
        self.client.logout()

        response = self.client.get('/gerencial/pedidos/exportar/')

        self.assertEqual(response.status_code, 302)
        self.assertIn('/gerencial/entrar/', response['Location'])


class DashboardAggregationCharacterizationTest(TestCase):
    """Caracterização das agregações do painel gerencial (D-003).

    ATENÇÃO: congela o comportamento ATUAL, que é um bug. As somas fazem JOIN
    com `items`, então o `shipping_cost` do pedido é somado UMA VEZ POR ITEM.
    O total do pedido (`Order.total`, correto) e o faturamento do painel
    divergem. A correção (R2) deve agregar itens e frete separadamente.
    """

    def setUp(self):
        self.manager = User.objects.create_superuser(
            username='gerente', email='gerente@example.com',
            password='senha-de-teste-forte',
        )
        self.client.force_login(self.manager)

        category = Category.objects.create(name='Roupas', slug='roupas')
        product = Product.objects.create(
            category=category, name='Camisa', slug='camisa',
            description='Desc', price=Decimal('10.00'), stock=10, available=True,
        )
        self.order = Order.objects.create(
            full_name='Cliente Teste', email='cliente@example.com',
            phone='11999999999', address='Rua A', city='São Paulo',
            state='SP', zip_code='01001-001', shipping_cost=Decimal('20.00'),
        )
        OrderItem.objects.create(order=self.order, product=product, price=Decimal('10.00'), quantity=1)
        OrderItem.objects.create(order=self.order, product=product, price=Decimal('10.00'), quantity=1)
        self.product = product

    def test_frete_e_contado_uma_vez_por_item_no_faturamento(self):
        response = self.client.get('/gerencial/')

        self.assertEqual(response.status_code, 200)
        # Valor correto: itens (20) + frete (20) = 40 — é o que Order.total diz.
        self.assertEqual(self.order.total, Decimal('40.00'))
        # Valor exibido hoje: (10 + 20) + (10 + 20) = 60 (frete duplicado).
        self.assertEqual(response.context['revenue_month'], Decimal('60.00'))
