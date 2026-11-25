from django.urls import path

from . import views

app_name = 'memes'

urlpatterns = [
    path('', views.meme_list, name='list'),
    path('<int:pk>/vote/', views.meme_vote, name='vote'),
    path('<int:pk>/delete/', views.meme_delete, name='delete'),
    path('<int:pk>/comments/', views.meme_comment_create, name='comment_create'),
    path('<int:pk>/comments/<int:comment_pk>/delete/', views.meme_comment_delete, name='comment_delete'),
]
