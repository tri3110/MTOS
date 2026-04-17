from django.urls import path
from .views import (
    CartView,
    CartAddView,
)

urlpatterns = [
    path('cart/sync/', CartView.as_view(), name='cart_sync'),
    path('cart/add/', CartAddView.as_view(), name='cart_add'),
    path('cart/delete/<int:id>/', CartAddView.as_view(), name='cart_delete'),
    path('cart/update/<int:id>/', CartAddView.as_view(), name='cart_update'),
    path('cart/get/', CartAddView.as_view(), name='cart_get'),
]