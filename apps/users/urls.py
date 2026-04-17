from django.urls import path
from .views import (
    MeView,
    RegisterView,
    LoginView,
    LogoutView,
    RefreshTokenView,
    ChangePasswordView,
    ThemeSettingView,
    UserProfileView,
    SocialLoginView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh-token/', RefreshTokenView.as_view(), name='refresh_token'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('social-login/', SocialLoginView.as_view(), name='social_login'),
    path('me/', MeView.as_view(), name='user_info'),
    path('themes/', ThemeSettingView.as_view(), name='themes_setting'),
]