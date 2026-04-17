from django.urls import path
from apps.stores.views import StoreUserView, StoreView

urlpatterns = [
    path('stores/get/', StoreView.as_view(), name='get_stores'),
    path('stores/create/', StoreView.as_view(), name='create_stores'),
    path('stores/update/<int:id>/', StoreView.as_view(), name='update_stores'),
    path('stores/delete/<int:id>/', StoreView.as_view(), name='delete_stores'),

    path('stores/user/get/', StoreUserView.as_view(), name='delete_stores'),
]