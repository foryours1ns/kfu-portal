from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse


class PlaceQuerySet(models.QuerySet):
    def published(self):
        """Только те заведения, которые показываются на сайте."""
        return self.filter(is_published=True)

    def with_rating(self):
        """Добавляет к каждому заведению среднюю оценку и количество
        опубликованных отзывов."""
        published_reviews = models.Q(reviews__is_published=True)
        return self.annotate(
            average_rating=models.Avg('reviews__rating', filter=published_reviews),
            review_count=models.Count('reviews', filter=published_reviews),
        )


class Place(models.Model):
    """Заведение рядом с университетом: кофейня, столовая и так далее."""

    class Category(models.TextChoices):
        # Слева значение, которое хранится в базе, справа подпись для людей
        COFFEE = 'coffee', 'Кофейня'
        CANTEEN = 'canteen', 'Столовая'
        CAFE = 'cafe', 'Кафе'
        FASTFOOD = 'fastfood', 'Фастфуд'
        SHOP = 'shop', 'Магазин'

    name = models.CharField('название', max_length=100)
    category = models.CharField('категория', max_length=20, choices=Category.choices)
    address = models.CharField('адрес', max_length=200)
    description = models.TextField('описание', blank=True)

    # Координаты для метки на карте, шесть знаков после запятой — точность до ~10 см
    latitude = models.DecimalField(
        'широта',
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitude = models.DecimalField(
        'долгота',
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )

    is_published = models.BooleanField(
        'опубликовано',
        default=True,
        help_text='Снимите галочку, чтобы скрыть заведение с сайта, не удаляя его.',
    )

    objects = PlaceQuerySet.as_manager()

    class Meta:
        verbose_name = 'заведение'
        verbose_name_plural = 'заведения'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """Адрес страницы заведения. Благодаря этому методу в админке
        появляется кнопка «Смотреть на сайте»."""
        return reverse('places:detail', args=[self.pk])

    def review_count_label(self):
        """Подпись с количеством отзывов: «1 отзыв», «2 отзыва», «5 отзывов»."""
        count = getattr(self, 'review_count', 0) or 0
        rem100 = count % 100
        rem10 = count % 10
        if 11 <= rem100 <= 19:
            word = 'отзывов'
        elif rem10 == 1:
            word = 'отзыв'
        elif 2 <= rem10 <= 4:
            word = 'отзыва'
        else:
            word = 'отзывов'
        return f'{count} {word}'


class ReviewQuerySet(models.QuerySet):
    def published(self):
        """Только опубликованные отзывы."""
        return self.filter(is_published=True)


class Review(models.Model):
    """Отзыв и оценка заведения от студента или анонимного гостя."""

    place = models.ForeignKey(
        Place,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='заведение',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reviews',
        verbose_name='автор',
    )
    rating = models.PositiveSmallIntegerField(
        'оценка',
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    text = models.TextField('текст отзыва', max_length=1000)
    is_published = models.BooleanField(
        'опубликован',
        default=True,
        help_text='Анонимные отзывы скрыты до проверки модератором.',
    )
    created_at = models.DateTimeField('дата создания', auto_now_add=True)

    objects = ReviewQuerySet.as_manager()

    class Meta:
        verbose_name = 'отзыв'
        verbose_name_plural = 'отзывы'
        ordering = ['-created_at']
        constraints = [
            # Один авторизованный пользователь может оставить только один отзыв заведению
            models.UniqueConstraint(
                fields=['place', 'author'],
                condition=models.Q(author__isnull=False),
                name='unique_review_per_author',
            ),
        ]

    def __str__(self):
        author_name = self.author.username if self.author else 'Анонимно'
        return f'{author_name} — {self.place.name} ({self.rating}/5)'
