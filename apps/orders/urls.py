from django.urls import path
from apps.orders.views import OrderDetailView, AdminOrderView

urlpatterns = [
    path('orders/<int:id>/', OrderDetailView.as_view(), name='get_order'),
    path('orders/get/', AdminOrderView.as_view(), name='get_order_view'),
    path('orders/update/<int:id>/', AdminOrderView.as_view(), name='update_order_view'),
    path('orders/delete/<int:id>/', AdminOrderView.as_view(), name='delete_order_view'),
]