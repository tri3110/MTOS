from rest_framework_simplejwt.tokens import RefreshToken
from django.http import HttpResponseRedirect

def generate_jwt(strategy, backend, user, *args, **kwargs):

    refresh = RefreshToken.for_user(user)

    response = HttpResponseRedirect("http://localhost:3000/")

    response.set_cookie("access_token", str(refresh.access_token), httponly=True)
    response.set_cookie("refresh_token", str(refresh), httponly=True)

    return response