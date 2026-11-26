from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .context_processors import MAX_RECENT_NOTIFICATIONS
from .forms import ProfileForm, SignupForm
from .models import Notification, User


def signup(request):
    """Регистрация нового пользователя."""
    # Тем, кто уже вошёл, регистрироваться незачем
    if request.user.is_authenticated:
        return redirect('core:home')

    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            # save() сам хеширует пароль, в базу он в открытом виде не попадает
            user = form.save()
            # Сразу входим под новым пользователем
            login(request, user)
            return redirect('core:home')
    else:
        form = SignupForm()

    return render(request, 'accounts/signup.html', {'form': form})


def profile_detail(request, username):
    """Страница профиля: для владельца — сразу форма редактирования,
    для остальных — просмотр анкеты."""
    profile_user = get_object_or_404(User, username__iexact=username)
    is_own_profile = request.user == profile_user

    if request.method == 'POST':
        if not is_own_profile:
            return HttpResponseForbidden()
        if request.POST.get('remove_avatar'):
            if profile_user.avatar:
                profile_user.avatar.delete(save=False)
                profile_user.avatar = ''
                profile_user.save(update_fields=['avatar'])
            messages.success(request, 'Профиль обновлён')
            return redirect(profile_user.get_absolute_url())
        form = ProfileForm(request.POST, request.FILES, instance=profile_user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль обновлён')
            return redirect(profile_user.get_absolute_url())
    else:
        form = ProfileForm(instance=profile_user) if is_own_profile else None

    has_profile_info = any([
        profile_user.display_name,
        profile_user.faculty,
        profile_user.telegram,
        profile_user.bio,
    ])
    return render(request, 'accounts/profile_detail.html', {
        'profile_user': profile_user,
        'is_own_profile': is_own_profile,
        'has_profile_info': has_profile_info,
        'form': form,
    })


@login_required
def notifications_poll(request):
    """Возвращает JSON со счётчиком непрочитанных и списком последних уведомлений."""
    qs = request.user.notifications.all()
    unread_count = qs.filter(is_read=False).count()
    items = []
    for n in qs[:MAX_RECENT_NOTIFICATIONS]:
        local_dt = timezone.localtime(n.created_at)
        items.append({
            'id': n.pk,
            'message': n.message,
            'read_url': reverse('accounts:notification_read', args=[n.pk]),
            'is_read': n.is_read,
            'created_at': local_dt.strftime('%d.%m.%Y %H:%M'),
        })
    return JsonResponse({
        'unread_count': unread_count,
        'notifications': items,
    })


@login_required
@require_POST
def notifications_read_all(request):
    """Отмечает все уведомления текущего пользователя прочитанными."""
    request.user.notifications.filter(is_read=False).update(is_read=True)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'unread_count': 0})

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER', '')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect('core:home')


@login_required
def notification_read(request, pk):
    """Отмечает уведомление прочитанным и перенаправляет по его ссылке."""
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=['is_read'])

    if notification.link and url_has_allowed_host_and_scheme(
        notification.link,
        allowed_hosts={request.get_host()},
    ):
        return redirect(notification.link)
    return redirect('core:home')
