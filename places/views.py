from django.shortcuts import render

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
        }
        for place in places
    ]

    return render(request, 'places/place_list.html', {
        'places': places,
        'places_data': places_data,
        'category_filters': CATEGORY_FILTERS,
    })
