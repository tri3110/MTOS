import json

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.db import transaction
from apps.users.services import send_notification

from apps.users.authentication import CookieJWTAuthentication
from common.redis_client import redis_client
from common.constants import UserCache
from common.permissions import IsAdminOrReadOnly
from .serializers import (
    ThemeSerializer,
    UserCreateSerializer,
    UserSerializer,
    LoginSerializer,
    RefreshTokenSerializer,
    ChangePasswordSerializer,
    SocialLoginSerializer
)

import requests
from .models import ThemeSetting, User
from rest_framework_simplejwt.tokens import RefreshToken


class RegisterView(APIView):
    # def post(self, request):
    #     data = request.data

    #     user = User.objects.create_user(
    #         email=data.get('email'),
    #         password=data.get('password'),
    #         full_name=data.get('full_name'),
    #         phone=data.get('phone', '')
    #     )

    #     user.is_staff = True
    #     user.is_superuser = True
    #     user.save()

    #     return Response({
    #         "message": "Admin created",
    #         "user": UserSerializer(user).data
    #     }, status=201)
    
    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data["user"]

            refresh = RefreshToken.for_user(user)

            response = Response({
                "message": "Login success",
                "user": UserSerializer(user).data
            })

            response.set_cookie(
                key="access_token",
                value=str(refresh.access_token),
                httponly=True,
                secure=False,
                samesite="Lax",
                path="/",
            )

            response.set_cookie(
                key="refresh_token",
                value=str(refresh),
                httponly=True,
                secure=False,
                samesite="Lax",
                path="/",
            )

            response.set_cookie(
                key="is_admin",
                value=str(UserSerializer(user).data["is_admin"]),
                httponly=True,
                secure=False,
                samesite="Lax",
                path="/",
            )

            return response

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.COOKIES.get("refresh_token")
            if not refresh_token:
                return Response(
                    {"error": "No refresh token"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            token = RefreshToken(refresh_token)
            token.blacklist()
            response = Response(
                {"message": "Logout success"},
                status=status.HTTP_205_RESET_CONTENT
            )
            response.delete_cookie("access_token", path="/")
            response.delete_cookie("refresh_token", path="/")
            response.delete_cookie("is_admin", path="/")

            return response

        except TokenError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class RefreshTokenView(APIView):
    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        if serializer.is_valid():
            try:
                refresh_token = serializer.validated_data['refresh']
                token = RefreshToken(refresh_token)
                access_token = str(token.access_token)
                return Response({'access': access_token})
            except TokenError as e:
                return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user
        new_password = serializer.validated_data['new_password']
        user.set_password(new_password)
        user.save()

        return Response(
            {'message': 'Mật khẩu đã được cập nhật thành công'},
            status=status.HTTP_200_OK
        )


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    # Lấy thông tin user
    def get(self, request):
        try:
            serializer = UserSerializer(
                request.user, context={'request': request})
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Cập nhật thông tin user
    def put(self, request):
        try:
            user = request.user
            serializer = UserSerializer(
                user,
                data=request.data,
                partial=True,
                context={'request': request}
            )

            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            serializer.save()
            return Response({
                'success': True,
                'data': serializer.data,
                'message': 'Cập nhật thông tin thành công'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SocialLoginView(APIView):
    def post(self, request):
        serializer = SocialLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        provider = serializer.validated_data['provider']
        access_token = serializer.validated_data['access_token']

        if provider == 'google':
            user_info_url = 'https://www.googleapis.com/oauth2/v3/userinfo'
            headers = {'Authorization': f'Bearer {access_token}'}
            resp = requests.get(user_info_url, headers=headers)
            if resp.status_code != 200:
                return Response({'error': 'Invalid Google token'}, status=400)
            data = resp.json()
            email = data.get('email')
            social_id = data.get('sub')
            avatar = data.get('picture')
            full_name = data.get('name')
        elif provider == 'facebook':
            user_info_url = f'https://graph.facebook.com/me?fields=id,name,email,picture&access_token={access_token}'
            resp = requests.get(user_info_url)
            if resp.status_code != 200:
                return Response({'error': 'Invalid Facebook token'}, status=400)
            data = resp.json()
            email = data.get('email')
            social_id = data.get('id')
            avatar = data.get('picture', {}).get('data', {}).get('url')
            full_name = data.get('name')
        else:
            return Response({'error': 'Provider not supported'}, status=400)

        try:
            user = User.objects.get(provider=provider, social_id=social_id)
            # Cập nhật thông tin nếu cần
            user.email = email or user.email
            user.full_name = full_name or user.full_name
            user.avatar = avatar or user.avatar
            user.save()
        except User.DoesNotExist:
            user = User.objects.create_social_user(
                provider=provider,
                social_id=social_id,
                email=email,
                full_name=full_name,
                avatar=avatar,
                is_active=True,
                username=f'{provider}_{social_id}',
            )

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })
    
class MeView(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "user": UserSerializer(request.user).data
        })
    
class ThemeSettingView(APIView):

    def get(self, request):
        themes = ThemeSetting.objects
        serializer = ThemeSerializer(themes, many=True)

        result = {}
        for item in serializer.data:
            result[item["key"]] = item["value"]

        return Response(result)

class UserView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request):
        try:
            
            page = int(request.GET.get("page", 1))
            page_size = int(request.GET.get("page_size", 1))
            search = request.GET.get("search", "")

            cache_key = f"{UserCache.ACTIVE.key}:{page}:{page_size}:{search}"
            cached = redis_client.get(cache_key)
            if cached:
                return Response(json.loads(cached))
            
            qs = User.objects.filter(is_active=True)

            if search:
                qs = qs.filter(username__icontains=search)

            qs = qs.order_by("-id")
            total = qs.count()

            start = (page - 1) * page_size
            end = start + page_size

            users = qs[start:end]
            
            data = UserSerializer(users, many=True).data
            response = {
                "results": data,
                "total": total,
                "page": page,
                "page_size": page_size,
            }

            redis_client.set(cache_key, json.dumps(response), ex=UserCache.ACTIVE.ttl)

            return Response(response)
        
        except Exception as e:
            return Response({'message': 'Server error'})
        
    def patch(self, request):
        try:
            if not request.user.is_admin:
                return Response({"message": "Permission denied"}, status=403)

            data = request.data

            if not isinstance(data, list):
                return Response({"message": "Invalid payload"}, status=400)

            ids = [item.get("id") for item in data if item.get("id")]
            users = User.objects.filter(id__in=ids)

            user_map = {u.id: u for u in users}

            to_update = []

            for item in data:
                user_id = item.get("id")
                role = item.get("role")

                if role not in User.Role.values:
                    continue

                user = user_map.get(user_id)
                if not user:
                    continue

                if user.role != role:
                    send_notification(user_id, "Notification", "Your account is updated by " + role)

                    user.role = role
                    to_update.append(user)

            with transaction.atomic():
                if to_update:
                    User.objects.bulk_update(to_update, ["role"])

            self.clear_user_cache()
            
            return Response({
                "updated_ids": [u.id for u in to_update]
            })

        except Exception as e:
            return Response({"message": str(e)}, status=400)
        
    def clear_user_cache(self):
        for key in redis_client.scan_iter(UserCache.ACTIVE.key + ":*"):
            redis_client.delete(key)