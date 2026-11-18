from django.urls import path

from . import views

app_name = 'places'

urlpatterns = [
    path('', views.place_list, name='list'),
    path('<int:pk>/', views.place_detail, name='detail'),
    path('<int:pk>/reviews/<int:review_pk>/edit/', views.review_edit, name='review_edit'),
    path('<int:pk>/reviews/<int:review_pk>/delete/', views.review_delete, name='review_delete'),
]
