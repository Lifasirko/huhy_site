from django.urls import path
from .views import (
    CatalogView,
    ProductDetailView,
    CartView,
    CheckoutView,
    OrderSuccessView,
    PersonalCabinetView
)

app_name = 'shop'

urlpatterns = [
    path('', CatalogView.as_view(), name='shop_home'),  # Головна сторінка – каталог
    path('catalog/', CatalogView.as_view(), name='catalog'),
    path('product/<slug:slug>/', ProductDetailView.as_view(), name='product_detail'),
    path('cart/', CartView.as_view(), name='cart'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('order-success/', OrderSuccessView.as_view(), name='order_success'),
    path('cabinet/', PersonalCabinetView.as_view(), name='personal_cabinet'),
]
