from django.conf import settings
from django.db import models
from django.db.models.functions import Coalesce


class MemeQuerySet(models.QuerySet):
    def published(self):
        """Только одобренные модератором мемы."""
        return self.filter(is_published=True)

    def with_score(self):
        """Добавляет к каждому мему суммарный рейтинг (апвоуты минус даунвоуты)."""
        return self.annotate(
            score=Coalesce(models.Sum('votes__value'), 0),
        )


class Meme(models.Model):
    """Мем от студента: картинка, необязательная подпись и премодерация."""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='memes',
        verbose_name='автор',
    )
    image = models.ImageField('картинка', upload_to='memes/')
    caption = models.CharField('подпись', max_length=140, blank=True)
    is_published = models.BooleanField(
        'опубликован',
        default=False,
        help_text='Новые мемы скрыты до проверки модератором.',
    )
    created_at = models.DateTimeField('дата создания', auto_now_add=True)

    objects = MemeQuerySet.as_manager()

    class Meta:
        verbose_name = 'мем'
        verbose_name_plural = 'мемы'
        ordering = ['-created_at']

    def __str__(self):
        if self.caption:
            return f'{self.caption[:40]} ({self.author.username})'
        return f'Мем #{self.pk} от {self.author.username}'


class MemeVote(models.Model):
    """Голос пользователя за мем: апвоут (+1) или даунвоут (-1)."""

    class Value(models.IntegerChoices):
        UP = 1, 'За (+1)'
        DOWN = -1, 'Против (-1)'

    meme = models.ForeignKey(
        Meme,
        on_delete=models.CASCADE,
        related_name='votes',
        verbose_name='мем',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='meme_votes',
        verbose_name='пользователь',
    )
    value = models.SmallIntegerField('голос', choices=Value.choices)
    created_at = models.DateTimeField('дата', auto_now_add=True)

    class Meta:
        verbose_name = 'голос за мем'
        verbose_name_plural = 'голоса за мемы'
        constraints = [
            models.UniqueConstraint(
                fields=['meme', 'user'],
                name='unique_meme_vote_per_user',
            ),
        ]

    def __str__(self):
        sign = '+1' if self.value > 0 else '-1'
        return f'{self.user.username} → мем #{self.meme_id} ({sign})'
