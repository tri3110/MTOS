from django.urls import path
from apps.vouchers.views import VoucherView

urlpatterns = [
    path('vouchers/get/', VoucherView.as_view(), name='get_vouchers'),
    path('vouchers/create/', VoucherView.as_view(), name='create_vouchers'),
    path('vouchers/update/<int:id>/', VoucherView.as_view(), name='update_vouchers'),
    path('vouchers/delete/<int:id>/', VoucherView.as_view(), name='delete_vouchers'),
]