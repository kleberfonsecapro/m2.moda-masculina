from django.contrib.auth.models import User
from django.test import TestCase

from orders.models import Order


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
