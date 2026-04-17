from django.urls import path
from .views import (
    CategoryUserView,
    CategoryView,
    HomeDataView,
    ProductMenuView,
    ProductSearchView,
    ProductView,
    ToppingView,
    OptionGroupView,
)

urlpatterns = [
    path('products/get/', ProductView.as_view(), name='get_products'),
    path('products/create/', ProductView.as_view(), name='create_products'),
    path('products/update/<int:id>/', ProductView.as_view(), name='update_products'),
    path('products/delete/<int:id>/', ProductView.as_view(), name='delete_products'),

    path('categories/get/', CategoryView.as_view(), name='get_categories'),
    path('categories/create/', CategoryView.as_view(), name='create_categories'),
    path('categories/update/<int:id>/', CategoryView.as_view(), name='update_categories'),
    path('categories/delete/<int:id>/', CategoryView.as_view(), name='delete_categories'),

    path('toppings/get/', ToppingView.as_view(), name='get_toppings'),
    path('toppings/create/', ToppingView.as_view(), name='create_toppings'),
    path('toppings/update/<int:id>/', ToppingView.as_view(), name='update_toppings'),
    path('toppings/delete/<int:id>/', ToppingView.as_view(), name='delete_toppings'),

    path('option_group/get/', OptionGroupView.as_view(), name='get_option_group'),
    path('option_group/create/', OptionGroupView.as_view(), name='create_option_group'),
    path('option_group/update/<int:id>/', OptionGroupView.as_view(), name='update_option_group'),
    path('option_group/delete/<int:id>/', OptionGroupView.as_view(), name='delete_option_group'),

    path('products/search/', ProductSearchView.as_view(), name='search_products'),

    path('products/menu/', ProductMenuView.as_view(), name='menu_all'),
    path('products/menu/<slug:slug>', ProductMenuView.as_view(), name='menu_products'),

    path('home/get/', HomeDataView.as_view(), name='get_data_home'),
    path('home/categories/get/', CategoryUserView.as_view(), name='get_data_categories_home'),
]