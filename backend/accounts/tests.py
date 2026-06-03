from django.test import TestCase
from django.contrib.auth.models import User


class RegistrationTest(TestCase):
    def test_register_status(self):
        response = self.client.get('/accounts/registro/')
        self.assertEqual(response.status_code, 200)

    def test_register_uses_correct_template(self):
        response = self.client.get('/accounts/registro/')
        self.assertTemplateUsed(response, 'accounts/register.html')

    def test_register_creates_user_and_logs_in(self):
        response = self.client.post('/accounts/registro/', {
            'username': 'joaosilva',
            'first_name': 'João',
            'last_name': 'Silva',
            'email': 'joao@email.com',
            'password1': 'SenhaForte123!',
            'password2': 'SenhaForte123!',
        })
        self.assertRedirects(response, '/')
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.get()
        self.assertEqual(user.username, 'joaosilva')
        self.assertEqual(user.first_name, 'João')
        self.assertEqual(user.last_name, 'Silva')
        self.assertEqual(user.email, 'joao@email.com')

    def test_register_rejects_weak_password(self):
        response = self.client.post('/accounts/registro/', {
            'username': 'joaosilva',
            'first_name': 'João',
            'last_name': 'Silva',
            'email': 'joao@email.com',
            'password1': '123',
            'password2': '123',
        })
        self.assertEqual(User.objects.count(), 0)
        self.assertContains(response, 'muito curta')

    def test_register_rejects_mismatched_passwords(self):
        response = self.client.post('/accounts/registro/', {
            'username': 'joaosilva',
            'first_name': 'João',
            'last_name': 'Silva',
            'email': 'joao@email.com',
            'password1': 'SenhaForte123!',
            'password2': 'SenhaDiferente456!',
        })
        self.assertEqual(User.objects.count(), 0)
        self.assertContains(response, 'correspondem')

    def test_register_rejects_duplicate_username(self):
        User.objects.create_user(username='joaosilva', password='123')
        response = self.client.post('/accounts/registro/', {
            'username': 'joaosilva',
            'first_name': 'João',
            'last_name': 'Silva',
            'email': 'joao@email.com',
            'password1': 'SenhaForte123!',
            'password2': 'SenhaForte123!',
        })
        self.assertEqual(User.objects.count(), 1)
        self.assertContains(response, 'já existe')

    def test_register_requires_email(self):
        response = self.client.post('/accounts/registro/', {
            'username': 'joaosilva',
            'first_name': 'João',
            'last_name': 'Silva',
            'email': '',
            'password1': 'SenhaForte123!',
            'password2': 'SenhaForte123!',
        })
        self.assertEqual(User.objects.count(), 0)


class LoginTest(TestCase):
    def setUp(self):
        User.objects.create_user(username='teste', password='Senha123!')

    def test_login_status(self):
        response = self.client.get('/accounts/login/')
        self.assertEqual(response.status_code, 200)

    def test_login_uses_correct_template(self):
        response = self.client.get('/accounts/login/')
        self.assertTemplateUsed(response, 'accounts/login.html')

    def test_login_successful(self):
        response = self.client.post('/accounts/login/', {
            'username': 'teste',
            'password': 'Senha123!',
        })
        self.assertEqual(response.status_code, 302)

    def test_login_fails_with_wrong_password(self):
        response = self.client.post('/accounts/login/', {
            'username': 'teste',
            'password': 'senha_errada',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'erro')


class ProfileTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='teste', password='123',
            first_name='João', last_name='Silva',
            email='joao@email.com',
        )

    def test_profile_requires_login(self):
        response = self.client.get('/accounts/perfil/')
        self.assertEqual(response.status_code, 302)

    def test_profile_shows_user_data(self):
        self.client.login(username='teste', password='123')
        response = self.client.get('/accounts/perfil/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile.html')
        self.assertContains(response, 'Bem-vindo')
        self.assertContains(response, 'João')
        self.assertContains(response, 'joao@email.com')


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
