// Колокольчик уведомлений в шапке: выпадающий список, кнопка «Прочитать всё»
// и фоновое обновление каждые 10 секунд без перезагрузки страницы.
document.addEventListener('DOMContentLoaded', function () {
    var menu = document.querySelector('[data-notif-menu]');
    if (!menu) {
        return;
    }

    var POLL_INTERVAL_MS = 10000;
    var pollUrl = menu.dataset.pollUrl;
    var bellBtn = document.getElementById('notif-bell-btn');
    var badgeEl = document.getElementById('notif-badge');
    var dropdownEl = document.getElementById('notif-dropdown');
    var readAllForm = document.getElementById('notif-read-all-form');
    var listEl = document.getElementById('notif-list');
    var emptyEl = document.getElementById('notif-empty');

    function renderNotifications(data) {
        var unreadCount = data.unread_count || 0;
        badgeEl.textContent = unreadCount;
        badgeEl.hidden = unreadCount === 0;
        if (readAllForm) {
            readAllForm.hidden = unreadCount === 0;
        }

        var items = data.notifications || [];
        listEl.innerHTML = '';

        if (items.length === 0) {
            listEl.hidden = true;
            emptyEl.hidden = false;
            return;
        }

        items.forEach(function (item) {
            var li = document.createElement('li');
            li.className = 'notif-item' + (item.is_read ? '' : ' unread');

            var link = document.createElement('a');
            link.className = 'notif-link';
            link.href = item.read_url;

            var textSpan = document.createElement('span');
            textSpan.className = 'notif-text';
            textSpan.textContent = item.message;

            var timeSpan = document.createElement('span');
            timeSpan.className = 'notif-time';
            timeSpan.textContent = item.created_at;

            link.appendChild(textSpan);
            link.appendChild(timeSpan);
            li.appendChild(link);
            listEl.appendChild(li);
        });

        listEl.hidden = false;
        emptyEl.hidden = true;
    }

    function pollNotifications() {
        if (!pollUrl || document.hidden) {
            return;
        }
        fetch(pollUrl, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            credentials: 'same-origin'
        })
            .then(function (response) {
                if (!response.ok) {
                    throw new Error('Poll error');
                }
                return response.json();
            })
            .then(renderNotifications)
            .catch(function () {
                // Игнорируем временные сетевые ошибки при фоновом опросе
            });
    }

    function closeDropdown() {
        dropdownEl.hidden = true;
        bellBtn.setAttribute('aria-expanded', 'false');
    }

    bellBtn.addEventListener('click', function () {
        var willOpen = dropdownEl.hidden;
        dropdownEl.hidden = !willOpen;
        bellBtn.setAttribute('aria-expanded', String(willOpen));
        if (willOpen) {
            pollNotifications();
        }
    });

    document.addEventListener('click', function (event) {
        if (!dropdownEl.hidden && !menu.contains(event.target)) {
            closeDropdown();
        }
    });

    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' && !dropdownEl.hidden) {
            closeDropdown();
        }
    });

    if (readAllForm) {
        readAllForm.addEventListener('submit', function (event) {
            event.preventDefault();
            fetch(readAllForm.action, {
                method: 'POST',
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
                body: new FormData(readAllForm)
            })
                .then(function (response) {
                    if (!response.ok) {
                        throw new Error('Read all error');
                    }
                    return response.json();
                })
                .then(function () {
                    badgeEl.textContent = '0';
                    badgeEl.hidden = true;
                    readAllForm.hidden = true;
                    listEl.querySelectorAll('.notif-item.unread').forEach(function (el) {
                        el.classList.remove('unread');
                    });
                })
                .catch(function () {
                    readAllForm.submit();
                });
        });
    }

    setInterval(pollNotifications, POLL_INTERVAL_MS);

    document.addEventListener('visibilitychange', function () {
        if (!document.hidden) {
            pollNotifications();
        }
    });
});
