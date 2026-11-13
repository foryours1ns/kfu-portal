from django.test import TestCase
from django.urls import reverse

from .models import User


class SignupTests(TestCase):
    def test_signup_creates_user_and_logs_in(self):
        response = self.client.post(reverse('accounts:signup'), {
            'username': 'student',
            'password1': 'Zachet#2026ok',
            'password2': 'Zachet#2026ok',
        })
        self.assertRedirects(response, reverse('core:home'))
        user = User.objects.get(username='student')
        # В базе лежит хеш, а не сам пароль
        self.assertNotEqual(user.password, 'Zachet#2026ok')
        self.assertTrue(user.check_password('Zachet#2026ok'))
        # После регистрации пользователь сразу вошёл
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_password_without_special_characters_is_rejected(self):
        response = self.client.post(reverse('accounts:signup'), {
            'username': 'student',
            'password1': 'Zachet2026ok',
            'password2': 'Zachet2026ok',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'цифры и спецсимволы')
        self.assertFalse(User.objects.filter(username='student').exists())

    def test_password_without_uppercase_letters_is_rejected(self):
        response = self.client.post(reverse('accounts:signup'), {
            'username': 'student',
            'password1': 'qwe_1234',
            'password2': 'qwe_1234',
        })
        self.assertContains(response, 'заглавные и строчные латинские буквы')
        self.assertFalse(User.objects.exists())

    def test_password_with_spaces_is_rejected(self):
        response = self.client.post(reverse('accounts:signup'), {
            'username': 'student',
            'password1': '    1!qQ',
            'password2': '    1!qQ',
        })
        self.assertContains(response, 'Пароль не должен содержать пробелы.')
        self.assertFalse(User.objects.exists())

    def test_short_password_is_rejected(self):
        response = self.client.post(reverse('accounts:signup'), {
            'username': 'student',
            'password1': 'a1#',
            'password2': 'a1#',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='student').exists())

    def test_username_longer_than_15_characters_is_rejected(self):
        response = self.client.post(reverse('accounts:signup'), {
            'username': 'a' * 16,
            'password1': 'Zachet#2026ok',
            'password2': 'Zachet#2026ok',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.exists())

    def test_username_with_forbidden_characters_is_rejected(self):
        response = self.client.post(reverse('accounts:signup'), {
            'username': 'студент!',
            'password1': 'Zachet#2026ok',
            'password2': 'Zachet#2026ok',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Логин может содержать только латинские буквы')
        self.assertFalse(User.objects.exists())

    def test_username_is_unique_regardless_of_case(self):
        User.objects.create_user(username='student', password='Zachet#2026ok')
        response = self.client.post(reverse('accounts:signup'), {
            'username': 'Student',
            'password1': 'Zachet#2026ok',
            'password2': 'Zachet#2026ok',
        })
        self.assertContains(response, 'Этот логин уже занят')
        self.assertEqual(User.objects.count(), 1)


class LoginLogoutTests(TestCase):
    def setUp(self):
        User.objects.create_user(username='student', password='Zachet#2026ok')

    def test_login_with_correct_password(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'student',
            'password': 'Zachet#2026ok',
        })
        self.assertRedirects(response, reverse('core:home'))

    def test_login_with_wrong_password(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'student',
            'password': 'wrong-password',
        })
        self.assertContains(response, 'Неверный логин или пароль.')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_requires_post(self):
        self.client.login(username='student', password='Zachet#2026ok')
        # Обычный переход по ссылке не должен разлогинивать
        self.assertEqual(self.client.get(reverse('accounts:logout')).status_code, 405)
        self.client.post(reverse('accounts:logout'))
        self.assertNotIn('_auth_user_id', self.client.session)
