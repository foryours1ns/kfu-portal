from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse


class PlaceQuerySet(models.QuerySet):
    def published(self):
        """Только те заведения, которые показываются на сайте."""
        return self.filter(is_published=True)


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
