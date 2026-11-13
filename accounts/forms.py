from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError

from .models import USERNAME_MAX_LENGTH, USERNAME_MIN_LENGTH, User


class SignupForm(UserCreationForm):
    """Форма регистрации: логин и пароль дважды."""

    class Meta:
        model = User
        fields = ('username',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        username = self.fields['username']
        username.label = 'Логин'
        username.min_length = USERNAME_MIN_LENGTH
        username.help_text = 'От 3 до 15 символов: латинские буквы, цифры и нижние подчёркивания'
        username.error_messages['max_length'] = 'Логин должен быть от 3 до 15 символов.'

        self.fields['password1'].label = 'Пароль'
        # Вместо подсказки под паролем показываем список требований
        # (шаблон _password_rules.html)
        self.fields['password1'].help_text = ''
        self.fields['password2'].label = 'Пароль ещё раз'
        self.fields['password2'].help_text = ''

    def clean_username(self):
        username = self.cleaned_data['username']
        # Логины "Ivan" и "ivan" считаем одним и тем же
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError('Этот логин уже занят.')
        return username

    def validate_password_for_user(self, user, **kwargs):
        """Проверяет пароль по правилам из настроек (AUTH_PASSWORD_VALIDATORS)."""
        password = self.cleaned_data.get('password2')
        if password:
            try:
                password_validation.validate_password(password, user)
            except ValidationError as error:
                # Ошибку показываем под первым полем пароля
                self.add_error('password1', error)


class LoginForm(AuthenticationForm):
    """Форма входа с теми же подписями, что и при регистрации."""

    # Одно сообщение и для неверного логина, и для неверного пароля,
    # чтобы нельзя было узнать, какие логины существуют
    error_messages = {
        **AuthenticationForm.error_messages,
        'invalid_login': 'Неверный логин или пароль.',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Логин'
