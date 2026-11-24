from django.contrib import messages
from django.contrib.auth import login
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProfileForm, SignupForm
from .models import User


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
