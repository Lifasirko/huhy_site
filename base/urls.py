from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # Головна сторінка
    # path('get_events/', views.get_events_ajax, name='get_events_ajax'),
    path('api/events/', views.events_api, name='events_api'),
    path('api/filters/', views.get_filters, name='filters_api'),
    path('thank-you/', views.thank_you, name='thank_you'),
]
