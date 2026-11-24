// Загрузка нового аватара по клику на кружок и удаление текущего аватара по ссылке.
document.addEventListener('DOMContentLoaded', function () {
    var avatarInput = document.getElementById('id_avatar');
    if (avatarInput) {
        avatarInput.addEventListener('change', function () {
            if (avatarInput.files && avatarInput.files.length > 0) {
                avatarInput.form.submit();
            }
        });
    }

    var link = document.getElementById('remove-avatar-link');
    var removeInput = document.getElementById('remove-avatar-input');
    if (link && removeInput) {
        link.addEventListener('click', function (event) {
            event.preventDefault();
            if (window.confirm(link.dataset.confirm)) {
                removeInput.value = '1';
                removeInput.form.submit();
            }
        });
    }
});
