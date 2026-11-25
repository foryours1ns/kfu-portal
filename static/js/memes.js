// Страница мемов: раскрытие формы загрузки, удаление с подтверждением и голосование без перезагрузки.
document.addEventListener('DOMContentLoaded', function () {
    var toggle = document.getElementById('meme-upload-toggle');
    var uploadForm = document.getElementById('meme-upload-form');
    if (toggle && uploadForm) {
        toggle.addEventListener('click', function () {
            var isHidden = uploadForm.toggleAttribute('hidden');
            toggle.setAttribute('aria-expanded', String(!isHidden));
        });
    }

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
