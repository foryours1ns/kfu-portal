import string

from django.contrib.auth.password_validation import MinimumLengthValidator
from django.core.exceptions import ValidationError


class MinLengthValidator(MinimumLengthValidator):
    """Стандартная проверка длины из Django, только с нашим текстом ошибки."""

    def get_error_message(self):
        return f'Пароль должен быть не короче {self.min_length} символов.'

    def get_help_text(self):
        return self.get_error_message()


class CharacterTypesValidator:
    """Проверяет состав пароля.

    В пароле должны быть заглавные и строчные латинские буквы, цифры
    и спецсимволы, а пробелов быть не должно.
    """

    message = (
        'Пароль должен содержать заглавные и строчные латинские буквы, '
        'цифры и спецсимволы.'
    )

    spaces_message = 'Пароль не должен содержать пробелы.'

    def validate(self, password, user=None):
        # Пробелы запрещаем: иначе ими можно добить пароль до нужной длины
        if any(ch.isspace() for ch in password):
            raise ValidationError(self.spaces_message, code='password_has_spaces')

        has_upper = any(ch in string.ascii_uppercase for ch in password)
        has_lower = any(ch in string.ascii_lowercase for ch in password)
        has_digit = any(ch.isdigit() for ch in password)
        # Спецсимвол — всё, что не буква и не цифра
        has_special = any(not ch.isalnum() for ch in password)

        if not (has_upper and has_lower and has_digit and has_special):
            raise ValidationError(self.message, code='password_character_types')

    def get_help_text(self):
        return self.message
