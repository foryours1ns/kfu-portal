from django.shortcuts import render


def home(request):
    """Главная страница портала."""
    return render(request, 'core/home.html')
