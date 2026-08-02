from django.test import TestCase
from django.contrib.auth.models import User


class LogoutTest(TestCase):
    def setUp(self):
        User.objects.create_user(username='teste', password='123')

    def test_logout_logs_user_out(self):
        self.client.login(username='teste', password='123')
        response = self.client.post('/accounts/logout/')
        self.assertEqual(response.status_code, 302)

    def test_logout_redirects_to_home(self):
        self.client.login(username='teste', password='123')
        response = self.client.post('/accounts/logout/')
        self.assertRedirects(response, '/produtos/')
