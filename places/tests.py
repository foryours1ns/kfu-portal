from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

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


class PlaceListPageTests(TestCase):
    def test_page_opens_without_places(self):
        response = self.client.get(reverse('places:list'))
        self.assertEqual(response.status_code, 200)

    def test_page_shows_only_published_places(self):
        make_place(name='Видимая кофейня')
        make_place(name='Скрытая кофейня', is_published=False)
        response = self.client.get(reverse('places:list'))
        self.assertContains(response, 'Видимая кофейня')
        self.assertNotContains(response, 'Скрытая кофейня')

    def test_map_data_contains_coordinates(self):
        place = make_place(latitude='55.790400', longitude='49.121400')
        response = self.client.get(reverse('places:list'))
        self.assertEqual(response.context['places_data'], [{
            'id': place.pk,
            'name': 'Тестовая кофейня',
            'category': 'coffee',
            'category_label': 'Кофейня',
            'address': 'ул. Кремлёвская, 18',
            'lat': 55.7904,
            'lng': 49.1214,
            'url': f'/places/{place.pk}/',
        }])

    def test_list_links_to_place_page(self):
        place = make_place()
        response = self.client.get(reverse('places:list'))
        self.assertContains(response, f'href="/places/{place.pk}/"')


class PlaceDetailPageTests(TestCase):
    def test_page_shows_place(self):
        place = make_place(name='1804 Coffee', description='Кофе в главном корпусе.')
        response = self.client.get(reverse('places:detail', args=[place.pk]))
        self.assertContains(response, '1804 Coffee')
        self.assertContains(response, 'ул. Кремлёвская, 18')
        self.assertContains(response, 'Кофе в главном корпусе.')

    def test_page_without_description(self):
        place = make_place()
        response = self.client.get(reverse('places:detail', args=[place.pk]))
        self.assertContains(response, 'Описания пока нет.')

    def test_unpublished_place_is_not_found(self):
        place = make_place(is_published=False)
        response = self.client.get(reverse('places:detail', args=[place.pk]))
        self.assertEqual(response.status_code, 404)

    def test_missing_place_is_not_found(self):
        response = self.client.get(reverse('places:detail', args=[9999]))
        self.assertEqual(response.status_code, 404)
