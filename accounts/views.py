from django.contrib.auth import login
from django.shortcuts import redirect, render

from .forms import SignupForm


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
