from django.urls import path
from apps.payments.views import MomoIPNView, PaymentView

urlpatterns = [
    path('payment/', PaymentView.as_view(), name='payment'),
    path("momo-ipn/", MomoIPNView.as_view()),
]