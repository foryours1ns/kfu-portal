from django.conf import settings
from django.conf.urls.static import static as media_static
from django.contrib import admin
from django.urls import include, path
from django.templatetags.static import static
from django.views.generic import RedirectView, TemplateView

urlpatterns = [
    # Браузер сам запрашивает иконки в корне на страницах, где они не указаны
    # (например, в админке), поэтому отдаём по этим адресам нашу иконку
    path('favicon.ico', RedirectView.as_view(url=static('img/favicon.svg'))),
    path('apple-touch-icon.png', RedirectView.as_view(url=static('img/favicon.svg'))),
    path('apple-touch-icon-precomposed.png', RedirectView.as_view(url=static('img/favicon.svg'))),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('places/', include('places.urls')),
    path('memes/', include('memes.urls')),
    path('', include('core.urls')),
]

# В режиме разработки Django сам раздаёт загруженные пользователями файлы
# и показывает наш шаблон 404 по адресу /404/
if settings.DEBUG:
    urlpatterns += [
        path('404/', TemplateView.as_view(template_name='404.html')),
    ]
    urlpatterns += media_static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
