// Выбор оценки звёздочками: подсветка при наведении курсора и фиксация по клику.
// Пока оценка не выбрана (все звёзды потухшие), кнопка отправки неактивна.
document.addEventListener('DOMContentLoaded', function () {
    var deleteButtons = document.querySelectorAll('[data-confirm]');
    deleteButtons.forEach(function (button) {
        button.addEventListener('click', function (event) {
            if (!window.confirm(button.dataset.confirm)) {
                event.preventDefault();
            }
        });
    });

    var widget = document.querySelector('[data-rating-widget]');
    if (!widget) {
        return;
    }

    var form = widget.closest('form');
    var submitButton = form ? form.querySelector('button[type="submit"]') : null;
    var starsBox = widget.querySelector('.star-rating-stars');
    var items = widget.querySelectorAll('.star-rating-item');

    function getCheckedValue() {
        var checked = widget.querySelector('input[name="rating"]:checked');
        return checked ? Number(checked.value) : 0;
    }

    function paint(activeValue) {
        items.forEach(function (item) {
            var value = Number(item.dataset.value);
            item.classList.toggle('active', value <= activeValue);
        });
    }

    function updateSubmitState() {
        var selected = getCheckedValue();
        paint(selected);
        if (submitButton) {
            submitButton.disabled = selected === 0;
        }
    }

    items.forEach(function (item) {
        var input = item.querySelector('input[name="rating"]');

        item.addEventListener('mouseenter', function () {
            paint(Number(item.dataset.value));
        });

        input.addEventListener('change', updateSubmitState);
    });

    starsBox.addEventListener('mouseleave', function () {
        paint(getCheckedValue());
    });

    if (form) {
        form.addEventListener('submit', function (event) {
            if (getCheckedValue() === 0) {
                event.preventDefault();
            }
        });
    }

    updateSubmitState();
});
