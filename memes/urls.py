from django.urls import path

from . import views

app_name = 'memes'

urlpatterns = [
    path('', views.meme_list, name='list'),
    path('<int:pk>/vote/', views.meme_vote, name='vote'),
    path('<int:pk>/delete/', views.meme_delete, name='delete'),
]
