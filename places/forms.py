from django import forms
from django.core.exceptions import ValidationError

from .models import Review

RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]


class ReviewForm(forms.ModelForm):
    """Форма добавления и редактирования отзыва."""

    rating = forms.TypedChoiceField(
        label='Оценка',
        choices=RATING_CHOICES,
        coerce=int,
        error_messages={
            'required': 'Выберите оценку от 1 до 5.',
            'invalid_choice': 'Оценка должна быть числом от 1 до 5.',
        },
    )

    class Meta:
        model = Review
        fields = ('rating', 'text')
        labels = {
            'text': 'Отзыв',
        }
        widgets = {
            'text': forms.Textarea(attrs={'rows': 4}),
        }
        error_messages = {
            'text': {
                'required': 'Напишите текст отзыва.',
                'max_length': 'Отзыв не должен быть длиннее 1000 символов.',
            },
        }

    def clean_text(self):
        text = self.cleaned_data['text'].strip()
        if not text:
            raise ValidationError('Напишите текст отзыва.')
        return text
