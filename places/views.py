from django.shortcuts import get_object_or_404, render

from .models import Place

# Подписи для кнопок фильтра (во множественном числе)
CATEGORY_FILTERS = [
    (Place.Category.COFFEE, 'Кофейни'),
    (Place.Category.CANTEEN, 'Столовые'),
    (Place.Category.CAFE, 'Кафе'),
    (Place.Category.FASTFOOD, 'Фастфуд'),
    (Place.Category.SHOP, 'Магазины'),
]


def place_list(request):
    """Карта заведений со списком."""
    places = Place.objects.published()

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
        }
        for place in places
    ]

    return render(request, 'places/place_list.html', {
        'places': places,
        'places_data': places_data,
        'category_filters': CATEGORY_FILTERS,
    })


def place_detail(request, pk):
    """Страница одного заведения."""
    # Если заведения нет или оно скрыто, Django сам покажет страницу 404
    place = get_object_or_404(Place.objects.published(), pk=pk)

    # Координаты для маленькой карты (static/js/place-map.js)
    place_data = {
        'name': place.name,
        'lat': float(place.latitude),
        'lng': float(place.longitude),
    }

    return render(request, 'places/place_detail.html', {
        'place': place,
        'place_data': place_data,
    })
