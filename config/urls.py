from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
]

# В режиме разработки Django вместо шаблона 404.html показывает свою
# отладочную страницу, поэтому добавляем адрес, чтобы посмотреть наш шаблон.
if settings.DEBUG:
    urlpatterns += [
        path('404/', TemplateView.as_view(template_name='404.html')),
    ]
