// Страница мемов: раскрытие формы загрузки и комментариев, ответ на комментарий,
// удаление с подтверждением и голосование без перезагрузки.
document.addEventListener('DOMContentLoaded', function () {
    var toggle = document.getElementById('meme-upload-toggle');
    var uploadForm = document.getElementById('meme-upload-form');
    if (toggle && uploadForm) {
        toggle.addEventListener('click', function () {
            var isHidden = uploadForm.toggleAttribute('hidden');
            toggle.setAttribute('aria-expanded', String(!isHidden));
        });
    }

    var commentToggles = document.querySelectorAll('[data-comments-toggle]');
    commentToggles.forEach(function (btn) {
        var box = document.getElementById(btn.dataset.commentsToggle);
        if (!box) {
            return;
        }
        btn.addEventListener('click', function () {
            var isHidden = box.toggleAttribute('hidden');
            btn.setAttribute('aria-expanded', String(!isHidden));
        });
    });

    var replyButtons = document.querySelectorAll('[data-reply-user]');
    replyButtons.forEach(function (btn) {
        btn.addEventListener('click', function () {
            var textarea = document.getElementById(btn.dataset.replyTarget);
            if (!textarea) {
                return;
            }
            var prefix = btn.dataset.replyUser + ', ';
            var current = textarea.value.replace(/^[A-Za-z0-9_]{3,15},\s*/, '');
            textarea.value = prefix + current;
            textarea.focus();
            textarea.setSelectionRange(textarea.value.length, textarea.value.length);
        });
    });

    var deleteButtons = document.querySelectorAll('[data-confirm]');
    deleteButtons.forEach(function (button) {
        button.addEventListener('click', function (event) {
            if (!window.confirm(button.dataset.confirm)) {
                event.preventDefault();
            }
        });
    });

    var voteForms = document.querySelectorAll('[data-vote-form]');
    voteForms.forEach(function (form) {
        var buttons = form.querySelectorAll('button[name="value"]');
        var scoreEl = form.querySelector('[data-vote-score]');
        var upBtn = form.querySelector('.vote-up');
        var downBtn = form.querySelector('.vote-down');

        buttons.forEach(function (btn) {
            btn.addEventListener('click', function (event) {
                event.preventDefault();
                var data = new FormData(form);
                data.set('value', btn.value);

                fetch(form.action, {
                    method: 'POST',
                    headers: { 'X-Requested-With': 'XMLHttpRequest' },
                    body: data
                })
                    .then(function (response) {
                        if (!response.ok) {
                            throw new Error('Vote error');
                        }
                        return response.json();
                    })
                    .then(function (result) {
                        scoreEl.textContent = result.score;
                        upBtn.classList.toggle('active', result.user_vote === 1);
                        downBtn.classList.toggle('active', result.user_vote === -1);
                    })
                    .catch(function () {
                        form.submit();
                    });
            });
        });
    });
});
