// Форма регистрации:
// 1) отмечает галочками выполненные требования к паролю прямо во время ввода;
// 2) не даёт нажать «Зарегистрироваться», пока не заполнены все поля
//    и не выполнены все требования.
// Это только удобство: настоящая проверка идёт на сервере
// (accounts/validators.py), потому что JavaScript в браузере можно отключить.
document.addEventListener('DOMContentLoaded', function () {
    var username = document.getElementById('id_username');
    var password = document.getElementById('id_password1');
    var passwordAgain = document.getElementById('id_password2');
    var list = document.getElementById('password-rules');
    if (!username || !password || !passwordAgain || !list) {
        return;
    }
    var button = password.form.querySelector('button[type="submit"]');

    // Название правила совпадает с атрибутом data-rule у пункта списка
    var rules = {
        // Пробелы в пароле запрещены, поэтому в длину их не засчитываем
        length: function (value) { return value.replace(/\s/g, '').length >= 8; },
        upper: function (value) { return /[A-Z]/.test(value); },
        lower: function (value) { return /[a-z]/.test(value); },
        digit: function (value) { return /\d/.test(value); },
        // Спецсимвол — всё, что не буква, не цифра и не пробел
        special: function (value) { return /[^\p{L}\p{N}\s]/u.test(value); }
    };

    // Пункт «Без пробелов» скрыт и появляется, только если в пароле есть пробел
    var spacesItem = list.querySelector('[data-rule="spaces"]');

    function update() {
        var allRulesDone = true;
        var items = list.querySelectorAll('li');
        for (var i = 0; i < items.length; i++) {
            var check = rules[items[i].dataset.rule];
            if (check) {
                var done = check(password.value);
                items[i].classList.toggle('done', done);
                allRulesDone = allRulesDone && done;
            }
        }

        var hasSpaces = /\s/.test(password.value);
        spacesItem.hidden = !hasSpaces;

        var allFilled = username.value.trim() !== '' && passwordAgain.value !== '';
        button.disabled = !(allFilled && allRulesDone && !hasSpaces);
    }

    username.addEventListener('input', update);
    password.addEventListener('input', update);
    passwordAgain.addEventListener('input', update);
    update();
});
