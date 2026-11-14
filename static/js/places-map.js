// Карта заведений.
// Слева список, справа карта. В списке остаются только те заведения, которые
// сейчас видны на карте и подходят под выбранную категорию.
document.addEventListener('DOMContentLoaded', function () {
    var page = document.getElementById('map-page');
    var list = document.getElementById('map-list');
    var count = document.getElementById('map-count');
    var empty = document.getElementById('map-empty');
    var filters = document.getElementById('map-filters');
    var toggle = document.getElementById('map-toggle');

    // Данные, которые Django положил на страницу (см. places/views.py)
    var places = JSON.parse(document.getElementById('places-data').textContent);

    var START_CENTER = [55.7920, 49.1223];   // корпус КФУ на Кремлёвской, 35
    var START_ZOOM = 18;                     // чем больше число, тем крупнее
    var MARKER = { radius: 8, color: '#fff', weight: 2, fillColor: '#222', fillOpacity: 1 };
    var MARKER_ACTIVE = { radius: 10, fillColor: '#e8590c' };

    // --- Карта и подложка ---
    var map = L.map('map').setView(START_CENTER, START_ZOOM);
    map.zoomControl.setPosition('topright');
    // Убираем из подписи слово Leaflet; сама подпись OpenStreetMap обязательна
    map.attributionControl.setPrefix(false);
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);

    // --- Метки ---
    var activeCategory = '';   // пустая строка значит «все категории»
    var activeId = null;       // заведение, у которого сейчас открыто окошко

    places.forEach(function (place) {
        place.marker = L.circleMarker([place.lat, place.lng], MARKER);
        place.marker.bindPopup(buildPopup(place));
        place.marker.on('popupopen', function () { setActive(place.id); });
        place.marker.on('popupclose', function () { setActive(null); });
        place.item = list.querySelector('li[data-id="' + place.id + '"]');
        place.item.querySelector('button').addEventListener('click', function () {
            place.marker.openPopup();
        });
    });

    // Содержимое окошка собираем из элементов, а не строкой с HTML:
    // так название из базы не сможет подсунуть на страницу чужой код
    function buildPopup(place) {
        var box = document.createElement('div');
        var name = document.createElement('strong');
        name.textContent = place.name;
        var meta = document.createElement('div');
        meta.textContent = place.category_label + ' · ' + place.address;
        box.appendChild(name);
        box.appendChild(meta);
        return box;
    }

    function setActive(id) {
        activeId = id;
        places.forEach(function (place) {
            var isActive = place.id === id;
            place.marker.setStyle(isActive ? MARKER_ACTIVE : MARKER);
            place.marker.setRadius(isActive ? MARKER_ACTIVE.radius : MARKER.radius);
            place.item.classList.toggle('active', isActive);
        });
    }

    // --- Главная функция: что показывать на карте и в списке ---
    function update() {
        var bounds = map.getBounds();   // видимая сейчас область карты
        var shown = 0;

        places.forEach(function (place) {
            var matches = activeCategory === '' || place.category === activeCategory;
            var onScreen = bounds.contains(place.marker.getLatLng());

            // Метка есть на карте, если заведение подходит под категорию
            if (matches && !map.hasLayer(place.marker)) {
                place.marker.addTo(map);
            } else if (!matches && map.hasLayer(place.marker)) {
                place.marker.remove();
            }

            // Строка в списке видна, если метка ещё и попала на экран
            place.item.hidden = !(matches && onScreen);
            if (matches && onScreen) {
                shown += 1;
            }
        });

        count.textContent = 'На экране: ' + shown;
        empty.hidden = shown > 0;
    }

    // Карту подвинули или изменили масштаб
    map.on('moveend', update);

    // --- Фильтр по категориям ---
    filters.addEventListener('click', function (event) {
        var chip = event.target.closest('.chip');
        if (!chip) {
            return;
        }
        activeCategory = chip.dataset.category;
        filters.querySelectorAll('.chip').forEach(function (other) {
            other.classList.toggle('active', other === chip);
        });
        map.closePopup();
        update();
    });

    // --- Кнопка «Скрыть список» ---
    toggle.addEventListener('click', function () {
        var hidden = page.classList.toggle('panel-hidden');
        toggle.textContent = hidden ? 'Показать список' : 'Скрыть список';
        toggle.setAttribute('aria-expanded', String(!hidden));
    });

    // Пока человек сам не трогал карту, держим её на начальной точке
    var userMoved = false;
    ['pointerdown', 'wheel', 'keydown'].forEach(function (eventName) {
        map.getContainer().addEventListener(eventName, function () {
            userMoved = true;
        });
    });

    // Leaflet запоминает размер карты в момент создания. Если блок с картой
    // потом меняет размер (страница дорисовалась, скрыли список, повернули
    // телефон), карте нужно об этом сообщить, иначе она рисуется кусками
    new ResizeObserver(function () {
        map.invalidateSize();
        if (!userMoved) {
            // Возвращаем центр на место: после смены размера он съезжает
            map.setView(START_CENTER, START_ZOOM, { animate: false });
        }
        update();
    }).observe(map.getContainer());

    update();
});
