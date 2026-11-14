"""Testes dos endpoints operacionais consumidos pelos healthchecks."""
import json
from unittest import mock

from django.db import OperationalError
from django.test import TestCase, override_settings


class HealthzTest(TestCase):
    def test_healthz_returns_ok_when_database_responds(self):
        response = self.client.get('/healthz')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {'status': 'ok'})

    def test_healthz_returns_503_when_database_is_down(self):
        with mock.patch(
            'm2shop.views.connection.ensure_connection',
            side_effect=OperationalError('senha do banco invalida'),
        ):
            response = self.client.get('/healthz')

        self.assertEqual(response.status_code, 503)
        self.assertEqual(json.loads(response.content), {'status': 'error'})
        # O corpo do probe nao pode virar vetor de reconhecimento (OWASP A09).
        self.assertNotIn('senha do banco invalida', response.content.decode())

    def test_healthz_does_not_redirect(self):
        response = self.client.get('/healthz')

        self.assertFalse(response.has_header('Location'))

    @override_settings(
        SECURE_SSL_REDIRECT=True,
        SECURE_REDIRECT_EXEMPT=[r'^healthz$'],
    )
    def test_healthz_is_exempt_from_ssl_redirect_in_production(self):
        # Reproduz producao (DEBUG=False): o probe chega via HTTP puro.
        response = self.client.get('/healthz')
        self.assertEqual(response.status_code, 200)

        # As demais rotas continuam sendo redirecionadas para HTTPS.
        self.assertEqual(self.client.get('/').status_code, 301)
