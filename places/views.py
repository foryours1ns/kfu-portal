from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ReviewForm
from .models import Place, Review

# Подписи для кнопок фильтра (во множественном числе)
CATEGORY_FILTERS = [
    (Place.Category.COFFEE, 'Кофейни'),
    (Place.Category.CANTEEN, 'Столовые'),
    (Place.Category.CAFE, 'Кафе'),
    (Place.Category.FASTFOOD, 'Фастфуд'),
    (Place.Category.SHOP, 'Магазины'),
]


# Ключ в сессии браузера: словарь {str(place.pk): review.pk} для анонимных отзывов
SESSION_ANON_REVIEWS_KEY = 'anon_reviews'


def place_list(request):
    """Карта заведений со списком."""
    places = Place.objects.published().with_rating()

    # Те же заведения в виде простых словарей: шаблон превратит их в JSON,
    # а скрипт static/js/places-map.js расставит по ним метки на карте
    places_data = [
        {
            'id': place.pk,
            'name': place.name,
            'category': place.category,
            'category_label': place.get_category_display(),
            'address': place.address,
            'lat': float(place.latitude),
            'lng': float(place.longitude),
            'url': place.get_absolute_url(),
            'rating': (
                f'{place.average_rating:.2f}'.replace('.', ',')
                if place.review_count
                else None
            ),
            'review_count_label': (
                place.review_count_label() if place.review_count else None
            ),
        }
        for place in places
    ]

    return render(request, 'places/place_list.html', {
        'places': places,
        'places_data': places_data,
        'category_filters': CATEGORY_FILTERS,
    })


def place_detail(request, pk):
    """Страница одного заведения с отзывами и формой оценки."""
    # Если заведения нет или оно скрыто, Django сам покажет страницу 404
    place = get_object_or_404(Place.objects.published().with_rating(), pk=pk)

    user_review = None
    if request.user.is_authenticated:
        user_review = place.reviews.filter(author=request.user).first()
    else:
        anon_reviews = request.session.get(SESSION_ANON_REVIEWS_KEY, {})
        review_id = anon_reviews.get(str(place.pk))
        if review_id is not None:
            user_review = place.reviews.filter(pk=review_id, author__isnull=True).first()
            if user_review is None:
                # Если модератор удалил отзыв в админке, очищаем запись из сессии
                anon_reviews = dict(anon_reviews)
                anon_reviews.pop(str(place.pk), None)
                request.session[SESSION_ANON_REVIEWS_KEY] = anon_reviews

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if user_review is not None:
            # Защита на сервере: если отзыв уже есть (от аккаунта или в сессии),
            # не перезаписываем его и не создаём дубликат
            if request.user.is_authenticated:
                form.add_error(None, 'Вы уже оставили отзыв об этом месте.')
            else:
                form.add_error(None, 'Вы уже отправили отзыв об этом месте.')
        elif form.is_valid():
            review = form.save(commit=False)
            review.place = place
            if request.user.is_authenticated:
                review.author = request.user
                review.is_published = True
                review.save()
                messages.success(request, 'Ваш отзыв опубликован.')
            else:
                review.is_published = False
                review.save()
                anon_reviews = dict(request.session.get(SESSION_ANON_REVIEWS_KEY, {}))
                anon_reviews[str(place.pk)] = review.pk
                request.session[SESSION_ANON_REVIEWS_KEY] = anon_reviews
                messages.success(
                    request,
                    'Спасибо! Отзыв отправлен на модерацию и появится после проверки.',
                )
            return redirect('places:detail', pk=place.pk)
    else:
        form = ReviewForm()

    # Остальные опубликованные отзывы (свой отзыв показывается отдельным блоком)
    reviews = place.reviews.published().select_related('author')
    if user_review is not None:
        reviews = reviews.exclude(pk=user_review.pk)

    # Координаты для маленькой карты (static/js/place-map.js)
    place_data = {
        'name': place.name,
        'lat': float(place.latitude),
        'lng': float(place.longitude),
    }

    return render(request, 'places/place_detail.html', {
        'place': place,
        'place_data': place_data,
        'reviews': reviews,
        'user_review': user_review,
        'form': form,
    })


@login_required
def review_edit(request, pk, review_pk):
    """Редактирование собственного отзыва."""
    place = get_object_or_404(Place.objects.published(), pk=pk)
    review = get_object_or_404(Review, pk=review_pk, place=place, author=request.user)

    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, 'Отзыв обновлён.')
            return redirect('places:detail', pk=place.pk)
    else:
        form = ReviewForm(instance=review)

    return render(request, 'places/review_edit.html', {
        'place': place,
        'review': review,
        'form': form,
    })


@login_required
@require_POST
def review_delete(request, pk, review_pk):
    """Удаление собственного отзыва."""
    place = get_object_or_404(Place.objects.published(), pk=pk)
    review = get_object_or_404(Review, pk=review_pk, place=place, author=request.user)
    review.delete()
    messages.success(request, 'Отзыв удалён.')
    return redirect('places:detail', pk=place.pk)
