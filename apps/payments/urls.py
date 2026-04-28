from django.urls import path
from apps.payments.views import DistanceView, MomoIPNView, PaymentView

urlpatterns = [
    path('payment/', PaymentView.as_view(), name='payment'),
    path("momo-ipn/", MomoIPNView.as_view(), name='momo-ipn'),
    path("distance/", DistanceView.as_view(), name='distance'),
]