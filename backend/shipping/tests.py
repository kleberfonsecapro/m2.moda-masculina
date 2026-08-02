import io
import json
from decimal import Decimal
from unittest import mock

from django.test import TestCase, Client

from .models import ShippingConfig, ShippingRegion, ShippingRate
from .services import lookup_cep, quote


class QuoteCalculationTest(TestCase):
    def setUp(self):
        self.config = ShippingConfig.objects.create(cep_origem='01001000')
        ShippingRegion.objects.create(
            nome='Todo Brasil', cep_inicio='00000000', cep_fim='99999999', fator=Decimal('1.00')
        )

    def test_postal_weight_uses_cubic_when_larger(self):
        self.config.peso_padrao_kg = Decimal('0.50')
        self.config.save()
        ShippingRate.objects.create(nome='PAC', peso_min_kg=0, peso_max_kg=1, valor_base=Decimal('20.00'))
        options = quote('01310100')
        self.assertEqual(len(options), 1)
        self.assertEqual(options[0]['value'], Decimal('20.00'))

    def test_postal_weight_uses_real_weight_when_larger(self):
        self.config.peso_padrao_kg = Decimal('5.00')
        self.config.save()
        ShippingRate.objects.create(nome='PAC', peso_min_kg=0, peso_max_kg=10, valor_base=Decimal('40.00'))
        options = quote('01310100')
        self.assertEqual(options[0]['value'], Decimal('40.00'))

    def test_quote_applies_region_factor(self):
        ShippingRate.objects.create(nome='Sedex', peso_min_kg=0, peso_max_kg=1, valor_base=Decimal('20.00'))
        ShippingRegion.objects.create(
            nome='Norte', cep_inicio='60000000', cep_fim='69999999', fator=Decimal('1.25')
        )
        options = quote('69000000')
        self.assertEqual(options[0]['value'], Decimal('25.00'))

    def test_quote_picks_rate_by_weight_range(self):
        ShippingRate.objects.create(nome='PAC 1kg', peso_min_kg=0, peso_max_kg=1, valor_base=Decimal('20.00'))
        ShippingRate.objects.create(nome='PAC 2kg', peso_min_kg=2, peso_max_kg=3, valor_base=Decimal('30.00'))
        self.config.peso_padrao_kg = Decimal('2.50')
        self.config.save()
        options = quote('01310100')
        self.assertEqual(len(options), 1)
        self.assertEqual(options[0]['name'], 'PAC 2kg')

    def test_quote_free_shipping_above_threshold(self):
        self.config.frete_gratis_acima_de = Decimal('200.00')
        self.config.save()
        ShippingRate.objects.create(nome='Sedex', peso_min_kg=0, peso_max_kg=1, valor_base=Decimal('30.00'))
        options = quote('01310100', subtotal=Decimal('250.00'))
        self.assertEqual(options[0]['value'], Decimal('0.00'))

    def test_quote_does_not_apply_free_shipping_below_threshold(self):
        self.config.frete_gratis_acima_de = Decimal('200.00')
        self.config.save()
        ShippingRate.objects.create(nome='Sedex', peso_min_kg=0, peso_max_kg=1, valor_base=Decimal('30.00'))
        options = quote('01310100', subtotal=Decimal('100.00'))
        self.assertEqual(options[0]['value'], Decimal('30.00'))

    def test_quote_returns_empty_without_config(self):
        ShippingConfig.objects.all().delete()
        self.assertEqual(quote('01310100'), [])

    def test_quote_returns_empty_with_invalid_cep(self):
        ShippingRate.objects.create(nome='PAC', peso_min_kg=0, peso_max_kg=1, valor_base=Decimal('20.00'))
        self.assertEqual(quote('abc'), [])

    def test_quote_returns_multiple_services_ordered_by_price(self):
        ShippingRate.objects.create(nome='Sedex', peso_min_kg=0, peso_max_kg=1, valor_base=Decimal('35.00'))
        ShippingRate.objects.create(nome='PAC', peso_min_kg=0, peso_max_kg=1, valor_base=Decimal('20.00'))
        options = quote('01310100')
        self.assertEqual([o['name'] for o in options], ['PAC', 'Sedex'])


class ViaCepLookupTest(TestCase):
    def _mock_response(self, payload):
        raw = json.dumps(payload).encode('utf-8')
        response = mock.Mock()
        response.read.return_value = raw
        return response

    @mock.patch('shipping.services.urlopen')
    def test_lookup_cep_valid(self, mock_urlopen):
        mock_urlopen.return_value.__enter__.return_value = self._mock_response({
            'cep': '01310-100', 'logradouro': 'Av. Paulista',
            'localidade': 'São Paulo', 'uf': 'SP',
        })
        data = lookup_cep('01310-100')
        self.assertIsNotNone(data)
        self.assertEqual(data['uf'], 'SP')

    @mock.patch('shipping.services.urlopen')
    def test_lookup_cep_not_found(self, mock_urlopen):
        mock_urlopen.return_value.__enter__.return_value = self._mock_response({'erro': True})
        self.assertIsNone(lookup_cep('99999999'))

    @mock.patch('shipping.services.urlopen', side_effect=OSError('timeout'))
    def test_lookup_cep_network_error_returns_none(self, mock_urlopen):
        self.assertIsNone(lookup_cep('01310100'))

    def test_lookup_cep_invalid_input(self):
        self.assertIsNone(lookup_cep(''))
        self.assertIsNone(lookup_cep('abc'))


class ShippingQuoteViewTest(TestCase):
    def setUp(self):
        self.config = ShippingConfig.objects.create(cep_origem='01001000')
        ShippingRegion.objects.create(
            nome='Todo Brasil', cep_inicio='00000000', cep_fim='99999999', fator=Decimal('1.00')
        )
        ShippingRate.objects.create(nome='Sedex', peso_min_kg=0, peso_max_kg=1, valor_base=Decimal('30.00'))

    def test_view_rejects_invalid_cep(self):
        response = self.client.post(
            '/frete/calcular/',
            data=json.dumps({'cep': '123'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    @mock.patch('shipping.services.urlopen')
    def test_view_returns_options(self, mock_urlopen):
        payload = {'cep': '01310-100', 'localidade': 'São Paulo', 'uf': 'SP'}
        raw = json.dumps(payload).encode('utf-8')
        response_mock = mock.Mock()
        response_mock.read.return_value = raw
        mock_urlopen.return_value.__enter__.return_value = response_mock

        response = self.client.post(
            '/frete/calcular/',
            data=json.dumps({'cep': '01310-100'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['address'], 'São Paulo - SP')
        self.assertEqual(len(data['options']), 1)
        self.assertEqual(data['options'][0]['name'], 'Sedex')
        self.assertEqual(data['options'][0]['value'], '30.00')

    def test_view_requires_post(self):
        response = self.client.get('/frete/calcular/')
        self.assertEqual(response.status_code, 405)

    def test_view_requires_csrf_for_anonymous_forms(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(
            '/frete/calcular/',
            data=json.dumps({'cep': '01310100'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)


class CepLookupViewTest(TestCase):
    def test_view_requires_post(self):
        response = self.client.get('/frete/cep/')
        self.assertEqual(response.status_code, 405)

    def test_view_rejects_invalid_cep(self):
        response = self.client.post(
            '/frete/cep/',
            data=json.dumps({'cep': 'abc'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    @mock.patch('shipping.services.urlopen')
    def test_view_returns_address_data(self, mock_urlopen):
        payload = {
            'cep': '01310-100', 'logradouro': 'Av. Paulista',
            'bairro': 'Bela Vista', 'localidade': 'São Paulo', 'uf': 'SP',
        }
        raw = json.dumps(payload).encode('utf-8')
        response_mock = mock.Mock()
        response_mock.read.return_value = raw
        mock_urlopen.return_value.__enter__.return_value = response_mock

        response = self.client.post(
            '/frete/cep/',
            data=json.dumps({'cep': '01310-100'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['logradouro'], 'Av. Paulista')
        self.assertEqual(data['bairro'], 'Bela Vista')
        self.assertEqual(data['localidade'], 'São Paulo')
        self.assertEqual(data['uf'], 'SP')

    @mock.patch('shipping.services.urlopen')
    def test_view_returns_404_for_unknown_cep(self, mock_urlopen):
        response_mock = mock.Mock()
        response_mock.read.return_value = json.dumps({'erro': True}).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = response_mock

        response = self.client.post(
            '/frete/cep/',
            data=json.dumps({'cep': '99999999'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 404)
