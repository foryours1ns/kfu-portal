// Маленькая карта на странице заведения: одна метка по центру.
document.addEventListener('DOMContentLoaded', function () {
    // Координаты, которые Django положил на страницу (см. places/views.py)
    var place = JSON.parse(document.getElementById('place-data').textContent);
    var point = [place.lat, place.lng];

    var map = L.map('place-map', { scrollWheelZoom: false }).setView(point, 17);
    map.attributionControl.setPrefix(false);
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);

    L.circleMarker(point, {
        radius: 9, color: '#fff', weight: 2, fillColor: '#e8590c', fillOpacity: 1
    }).addTo(map);

    // Если блок с картой изменил размер, сообщаем об этом карте
    // и возвращаем метку в центр
    new ResizeObserver(function () {
        map.invalidateSize();
        map.setView(point, map.getZoom(), { animate: false });
    }).observe(map.getContainer());
});
