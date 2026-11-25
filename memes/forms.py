from django import forms
from django.core.exceptions import ValidationError

from .models import Meme, MemeComment

MAX_MEME_IMAGE_SIZE = 5 * 1024 * 1024  # 5 МБ


class MemeForm(forms.ModelForm):
    """Форма загрузки нового мема (отправляется на премодерацию)."""

    class Meta:
        model = Meme
        fields = ('image', 'caption')
        labels = {
            'image': 'Картинка',
            'caption': 'Подпись (необязательно)',
        }
        help_texts = {
            'image': 'JPG, PNG или WebP до 5 МБ',
            'caption': 'До 140 символов',
        }
        widgets = {
            'image': forms.FileInput(attrs={'accept': 'image/*'}),
        }
        error_messages = {
            'image': {
                'required': 'Выберите картинку.',
                'invalid_image': 'Загрузите корректное изображение.',
            },
            'caption': {
                'max_length': 'Подпись не должна быть длиннее 140 символов.',
            },
        }

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image and hasattr(image, 'size') and image.size > MAX_MEME_IMAGE_SIZE:
            raise ValidationError('Размер файла не должен превышать 5 МБ.')
        return image

    def clean_caption(self):
        return self.cleaned_data['caption'].strip()


class MemeCommentForm(forms.ModelForm):
    """Форма добавления комментария к мему."""

    class Meta:
        model = MemeComment
        fields = ('text',)
        labels = {
            'text': 'Комментарий',
        }
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Написать комментарий…',
            }),
        }
        error_messages = {
            'text': {
                'required': 'Напишите текст комментария.',
                'max_length': 'Комментарий не должен быть длиннее 300 символов.',
            },
        }

    def clean_text(self):
        text = self.cleaned_data['text'].strip()
        if not text:
            raise ValidationError('Напишите текст комментария.')
        return text
