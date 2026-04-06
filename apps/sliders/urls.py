from django.urls import path

from apps.sliders.views import SliderView, SliderHomeView

urlpatterns = [
    path('sliders/get/', SliderView.as_view(), name='get_sliders'),
    path('sliders/create/', SliderView.as_view(), name='create_sliders'),
    path('sliders/update/<int:id>/', SliderView.as_view(), name='update_sliders'),
    path('sliders/delete/<int:id>/', SliderView.as_view(), name='delete_sliders'),
    path('sliders/home/get/', SliderHomeView.as_view(), name='get_sliders_home'),
]