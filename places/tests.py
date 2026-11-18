from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from .models import Place, Review

User = get_user_model()


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

    def test_review_count_label_pluralization(self):
        place = make_place()
        cases = [
            (0, '0 отзывов'),
            (1, '1 отзыв'),
            (2, '2 отзыва'),
            (3, '3 отзыва'),
            (4, '4 отзыва'),
            (5, '5 отзывов'),
            (11, '11 отзывов'),
            (13, '13 отзывов'),
            (19, '19 отзывов'),
            (21, '21 отзыв'),
            (22, '22 отзыва'),
            (25, '25 отзывов'),
            (111, '111 отзывов'),
            (154, '154 отзыва'),
        ]
        for count, expected in cases:
            with self.subTest(count=count):
                place.review_count = count
                self.assertEqual(place.review_count_label(), expected)


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
            'rating': None,
            'review_count_label': None,
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

    def test_page_shows_empty_reviews_message(self):
        place = make_place()
        response = self.client.get(reverse('places:detail', args=[place.pk]))
        self.assertContains(response, 'Отзывов пока нет')

    def test_page_shows_average_rating_rounded_to_two_decimals(self):
        place = make_place()
        Review.objects.create(place=place, rating=5, text='Отлично')
        Review.objects.create(place=place, rating=4, text='Хорошо')
        Review.objects.create(place=place, rating=4, text='Неплохо')
        # Скрытый отзыв не должен влиять на средний рейтинг
        Review.objects.create(place=place, rating=1, text='Скрыт', is_published=False)

        response = self.client.get(reverse('places:detail', args=[place.pk]))
        self.assertContains(response, '★ 4,33</span> · 3 отзыва')


class ReviewModelTests(TestCase):
    def test_rating_out_of_range_is_rejected(self):
        place = make_place()
        review = Review(place=place, rating=6, text='Слишком высоко')
        with self.assertRaises(ValidationError):
            review.full_clean()

    def test_unique_review_per_authenticated_author(self):
        place = make_place()
        user = User.objects.create_user(username='student1')
        Review.objects.create(place=place, author=user, rating=5, text='Первый отзыв')
        with self.assertRaises(IntegrityError):
            Review.objects.create(place=place, author=user, rating=4, text='Второй отзыв')

    def test_multiple_anonymous_reviews_are_allowed(self):
        place = make_place()
        Review.objects.create(place=place, rating=5, text='Аноним 1', is_published=False)
        Review.objects.create(place=place, rating=4, text='Аноним 2', is_published=False)
        self.assertEqual(place.reviews.count(), 2)


class ReviewFlowTests(TestCase):
    def setUp(self):
        self.place = make_place()
        self.user = User.objects.create_user(username='ivan')

    def test_authenticated_user_review_is_published_immediately(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('places:detail', args=[self.place.pk]),
            {'rating': 5, 'text': 'Отличный кофе между парами!'},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        review = Review.objects.get(place=self.place, author=self.user)
        self.assertTrue(review.is_published)
        self.assertContains(response, 'Отличный кофе между парами!')
        self.assertContains(response, '★ 5,00</span> · 1 отзыв')
        # Форма скрыта, вместо неё показан блок со своим отзывом и кнопками
        self.assertNotContains(response, 'Отправить отзыв')
        self.assertContains(response, 'Вы уже оставили отзыв об этом месте:')
        self.assertContains(response, 'Изменить')
        self.assertContains(response, 'Удалить')

    def test_duplicate_review_post_from_authenticated_user_is_rejected(self):
        self.client.force_login(self.user)
        Review.objects.create(
            place=self.place,
            author=self.user,
            rating=5,
            text='Исходный отзыв',
        )

        response = self.client.post(
            reverse('places:detail', args=[self.place.pk]),
            {'rating': 1, 'text': 'Попытка перезаписать через POST'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Вы уже оставили отзыв об этом месте.')
        # Отзыв не перезаписался и дубликат не появился
        self.assertEqual(Review.objects.filter(place=self.place).count(), 1)
        review = Review.objects.get(place=self.place, author=self.user)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.text, 'Исходный отзыв')

    def test_anonymous_review_goes_to_moderation(self):
        response = self.client.post(
            reverse('places:detail', args=[self.place.pk]),
            {'rating': 4, 'text': 'Вкусная выпечка'},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        review = Review.objects.get(place=self.place)
        self.assertIsNone(review.author)
        self.assertFalse(review.is_published)
        self.assertContains(
            response,
            'Спасибо! Отзыв отправлен на модерацию и появится после проверки.',
        )
        # Пока модератор не одобрил, сам текст отзыва и рейтинг не показываются
        self.assertNotContains(response, 'Вкусная выпечка')
        self.assertContains(response, 'Отзывов пока нет')
        # После отправки форма для этого же гостя скрыта
        self.assertNotContains(response, 'Отправить отзыв')
        self.assertContains(
            response,
            'Вы уже отправили отзыв об этом месте — он появится на странице после проверки модератором.',
        )

    def test_duplicate_anonymous_review_in_same_session_is_rejected(self):
        self.client.post(
            reverse('places:detail', args=[self.place.pk]),
            {'rating': 4, 'text': 'Первый анонимный отзыв'},
        )
        response = self.client.post(
            reverse('places:detail', args=[self.place.pk]),
            {'rating': 1, 'text': 'Попытка спама вторым отзывом'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Вы уже отправили отзыв об этом месте.')
        self.assertEqual(Review.objects.filter(place=self.place).count(), 1)

    def test_anonymous_review_after_moderation_shows_published_state(self):
        self.client.post(
            reverse('places:detail', args=[self.place.pk]),
            {'rating': 4, 'text': 'Анонимный отзыв после одобрения'},
        )
        review = Review.objects.get(place=self.place)
        review.is_published = True
        review.save()

        response = self.client.get(reverse('places:detail', args=[self.place.pk]))
        self.assertNotContains(
            response,
            'он появится на странице после проверки модератором',
        )
        self.assertContains(response, 'Вы уже оставили отзыв об этом месте:')
        self.assertContains(response, 'Анонимный отзыв после одобрения')

    def test_anonymous_review_deleted_by_moderator_restores_form(self):
        self.client.post(
            reverse('places:detail', args=[self.place.pk]),
            {'rating': 2, 'text': 'Отклонённый отзыв'},
        )
        Review.objects.filter(place=self.place).delete()

        response = self.client.get(reverse('places:detail', args=[self.place.pk]))
        self.assertContains(response, 'Отправить отзыв')

    def test_blank_review_text_is_rejected(self):
        response = self.client.post(
            reverse('places:detail', args=[self.place.pk]),
            {'rating': 5, 'text': '   '},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Напишите текст отзыва.')
        self.assertFalse(Review.objects.exists())

    def test_new_review_form_has_no_preselected_stars(self):
        response = self.client.get(reverse('places:detail', args=[self.place.pk]))
        self.assertNotContains(response, 'checked')
        self.assertContains(response, 'name="rating" value="1" required')

    def test_review_without_rating_is_rejected(self):
        response = self.client.post(
            reverse('places:detail', args=[self.place.pk]),
            {'text': 'Отзыв с пустыми звёздами'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Выберите оценку от 1 до 5.')
        self.assertFalse(Review.objects.exists())

    def test_review_with_out_of_range_rating_is_rejected(self):
        for invalid_rating in (0, 6):
            with self.subTest(rating=invalid_rating):
                response = self.client.post(
                    reverse('places:detail', args=[self.place.pk]),
                    {'rating': invalid_rating, 'text': 'Неверная оценка'},
                )
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'Оценка должна быть числом от 1 до 5.')
                self.assertFalse(Review.objects.exists())

    def test_author_can_edit_own_review(self):
        self.client.force_login(self.user)
        review = Review.objects.create(
            place=self.place,
            author=self.user,
            rating=3,
            text='Было нормально',
        )

        response = self.client.post(
            reverse('places:review_edit', args=[self.place.pk, review.pk]),
            {'rating': 5, 'text': 'Стало отлично!'},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        review.refresh_from_db()
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.text, 'Стало отлично!')
        self.assertContains(response, 'Стало отлично!')

    def test_author_can_delete_own_review(self):
        self.client.force_login(self.user)
        review = Review.objects.create(
            place=self.place,
            author=self.user,
            rating=4,
            text='Удалю этот отзыв',
        )

        response = self.client.post(
            reverse('places:review_delete', args=[self.place.pk, review.pk]),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Review.objects.filter(pk=review.pk).exists())
        # После удаления форма снова доступна
        self.assertContains(response, 'Отправить отзыв')

    def test_other_user_cannot_edit_or_delete_review(self):
        review = Review.objects.create(
            place=self.place,
            author=self.user,
            rating=5,
            text='Чужой отзыв',
        )
        stranger = User.objects.create_user(username='stranger')
        self.client.force_login(stranger)

        edit_response = self.client.post(
            reverse('places:review_edit', args=[self.place.pk, review.pk]),
            {'rating': 1, 'text': 'Взлом'},
        )
        delete_response = self.client.post(
            reverse('places:review_delete', args=[self.place.pk, review.pk]),
        )
        self.assertEqual(edit_response.status_code, 404)
        self.assertEqual(delete_response.status_code, 404)
        review.refresh_from_db()
        self.assertEqual(review.text, 'Чужой отзыв')
