from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import Place


def make_place(**kwargs):
    """Создаёт заведение с данными по умолчанию, чтобы не повторять их в тестах."""
    data = {
        'name': 'Тестовая кофейня',
        'category': Place.Category.COFFEE,
        'address': 'ул. Кремлёвская, 18',
        'latitude': '55.790400',
        'longitude': '49.121400',
    }
    data.update(kwargs)
    return Place.objects.create(**data)


class PlaceModelTests(TestCase):
    def test_str_is_name(self):
        self.assertEqual(str(make_place(name='1804 Coffee')), '1804 Coffee')

    def test_published_hides_unpublished_places(self):
        visible = make_place(name='Видно')
        make_place(name='Скрыто', is_published=False)
        self.assertEqual(list(Place.objects.published()), [visible])

    def test_latitude_out_of_range_is_rejected(self):
        place = make_place()
        place.latitude = 155
        with self.assertRaises(ValidationError):
            place.full_clean()


class PlaceFixtureTests(TestCase):
    # Перед тестом Django загрузит places/fixtures/places.json
    fixtures = ['places']

    def test_fixture_loads_and_every_place_is_valid(self):
        self.assertTrue(Place.objects.exists())
        for place in Place.objects.all():
            # full_clean проверяет категорию, длины полей и диапазон координат
            place.full_clean()
