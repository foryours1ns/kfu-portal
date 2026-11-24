import io
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

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


class ProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='student')
        self.profile_url = reverse('accounts:profile', args=['student'])

    def test_empty_profile_shows_placeholder_for_visitors(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Профиль student')
        self.assertContains(response, 'data:image/svg+xml;utf8,')
        self.assertContains(response, 'Пользователь пока ничего о себе не указал.')
        self.assertNotContains(response, 'Сохранить')

    def test_filled_profile_displays_all_fields_and_telegram_link(self):
        self.user.display_name = 'Айдар'
        self.user.faculty = User.Faculty.ITIS
        self.user.telegram = 'aidar_kfu'
        self.user.bio = '2 курс, пишу на Python'
        self.user.save()

        response = self.client.get(reverse('accounts:profile', args=['STUDENT']))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Профиль student')
        self.assertContains(response, 'Айдар')
        self.assertContains(response, 'ИТИС')
        self.assertContains(response, 'href="https://t.me/aidar_kfu"')
        self.assertContains(response, '@aidar_kfu')
        self.assertContains(response, '2 курс, пишу на Python')

    def test_missing_profile_returns_404(self):
        response = self.client.get(reverse('accounts:profile', args=['nobody']))
        self.assertEqual(response.status_code, 404)

    def test_own_profile_opens_directly_with_edit_form(self):
        other = User.objects.create_user(username='other')
        self.client.force_login(self.user)

        own_response = self.client.get(self.profile_url)
        other_response = self.client.get(reverse('accounts:profile', args=[other.username]))

        self.assertContains(own_response, 'Сохранить')
        self.assertNotContains(other_response, 'Сохранить')

    def test_stranger_cannot_post_to_other_user_profile(self):
        other = User.objects.create_user(username='other')
        self.client.force_login(other)
        response = self.client.post(self.profile_url, {'display_name': 'Взлом'})
        self.assertEqual(response.status_code, 403)
        self.user.refresh_from_db()
        self.assertEqual(self.user.display_name, '')

    def test_user_can_update_profile_and_save_empty_fields(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.profile_url,
            {
                'display_name': '  Айдар  ',
                'faculty': User.Faculty.IVMIIT,
                'telegram': '  @aidar_kfu  ',
                'bio': '  Люблю кофе в 1804  ',
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.display_name, 'Айдар')
        self.assertEqual(self.user.faculty, User.Faculty.IVMIIT)
        self.assertEqual(self.user.telegram, 'aidar_kfu')
        self.assertEqual(self.user.bio, 'Люблю кофе в 1804')
        self.assertContains(response, 'Профиль обновлён')

        # Все пустые поля тоже спокойно сохраняются
        self.client.post(
            self.profile_url,
            {
                'display_name': '',
                'faculty': '',
                'telegram': '',
                'bio': '',
            },
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.display_name, '')
        self.assertEqual(self.user.faculty, '')
        self.assertEqual(self.user.telegram, '')
        self.assertEqual(self.user.bio, '')

    def test_display_name_longer_than_25_chars_is_rejected(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.profile_url,
            {
                'display_name': 'А' * 26,
                'faculty': '',
                'telegram': '',
                'bio': '',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Имя не должно быть длиннее 25 символов.')

    def test_invalid_telegram_username_is_rejected(self):
        self.client.force_login(self.user)
        invalid_cases = [
            ('ab', 'Юзернейм в Telegram должен быть от 5 до 32 символов.'),
            ('@ab', 'Юзернейм в Telegram должен быть от 5 до 32 символов.'),
            ('a' * 33, 'Юзернейм в Telegram должен быть от 5 до 32 символов.'),
            ('ivan!kfu', 'Юзернейм в Telegram может содержать только латинские буквы'),
            ('@@@', 'Укажите корректный юзернейм в Telegram.'),
        ]
        for bad_telegram, expected_error in invalid_cases:
            with self.subTest(telegram=bad_telegram):
                response = self.client.post(
                    self.profile_url,
                    {
                        'display_name': '',
                        'faculty': '',
                        'telegram': bad_telegram,
                        'bio': '',
                    },
                )
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, expected_error)

    def test_user_can_upload_and_remove_avatar(self):
        temp_media = tempfile.mkdtemp()
        try:
            with override_settings(MEDIA_ROOT=temp_media):
                self.client.force_login(self.user)
                buf = io.BytesIO()
                Image.new('RGB', (32, 32), color=(232, 89, 12)).save(buf, format='PNG')
                avatar_file = SimpleUploadedFile(
                    'avatar.png',
                    buf.getvalue(),
                    content_type='image/png',
                )

                response = self.client.post(
                    self.profile_url,
                    {
                        'avatar': avatar_file,
                        'display_name': 'Айдар',
                        'faculty': '',
                        'telegram': '',
                        'bio': '',
                    },
                    follow=True,
                )
                self.assertEqual(response.status_code, 200)
                self.user.refresh_from_db()
                self.assertTrue(bool(self.user.avatar))
                self.assertContains(response, self.user.avatar.url)

                # Удаление аватара кнопкой-ссылкой «Удалить текущий аватар»
                self.client.post(
                    self.profile_url,
                    {'remove_avatar': '1'},
                )
                self.user.refresh_from_db()
                self.assertFalse(bool(self.user.avatar))
        finally:
            shutil.rmtree(temp_media, ignore_errors=True)
