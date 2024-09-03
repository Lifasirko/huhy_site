from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # Головна сторінка
    path('get_events/', views.get_events_ajax, name='get_events_ajax'),
]
