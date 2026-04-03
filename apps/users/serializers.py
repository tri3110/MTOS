from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import serializers
from .models import User


class PasswordField(serializers.CharField):
    def __init__(self, **kwargs):
        kwargs.setdefault('style', {'input_type': 'password'})
        kwargs.setdefault('write_only', True)
        super().__init__(**kwargs)


class UserCreateSerializer(serializers.ModelSerializer):
    password = PasswordField(required=True)
    password_confirm = PasswordField(required=True)

    class Meta:
        model = User
        fields = ('email', 'password', 'password_confirm',
                  'full_name', 'phone')
        extra_kwargs = {
            'email': {'required': True},
            'full_name': {'required': True}
        }

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email đã được sử dụng")
        return value

    def validate_password(self, value):
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError(
                {"password_confirm": "Mật khẩu không trùng khớp"})
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            full_name=validated_data['full_name'],
            phone=validated_data.get('phone', '')
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'full_name',
            'phone',
            'role',
            'avatar',
            'is_staff_member',
            'is_admin'
        ]
        extra_kwargs = {
            'email': {'read_only': True},
            'role': {'read_only': True},
            'is_staff_member': {'read_only': True},
            'is_admin': {'read_only': True}
        }

    def validate_phone(self, value):
        # Thêm validation cho số điện thoại nếu cần
        if len(value) < 10:
            raise serializers.ValidationError("Số điện thoại không hợp lệ")
        return value


class LoginSerializer(serializers.Serializer):
    username_or_email = serializers.CharField(required=True)
    password = PasswordField(required=True)

    def validate(self, data):
        username_or_email = data.get('username_or_email')
        password = data.get('password')

        if not username_or_email or not password:
            raise serializers.ValidationError(
                "Tên đăng nhập/email và mật khẩu là bắt buộc")

        # Xác định là email hay username
        if '@' in username_or_email:
            # Tìm user bằng email
            try:
                user = User.objects.get(email=username_or_email)
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    "Thông tin đăng nhập không chính xác")
        else:
            # Tìm user bằng username (dành cho social user)
            try:
                user = User.objects.get(username=username_or_email)
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    "Thông tin đăng nhập không chính xác")

        # Kiểm tra mật khẩu
        if not user.check_password(password):
            raise serializers.ValidationError(
                "Thông tin đăng nhập không chính xác")

        # Kiểm tra tài khoản có active không
        if not user.is_active:
            raise serializers.ValidationError("Tài khoản đã bị vô hiệu hóa")

        # Kiểm tra nếu là social user thì không cho đăng nhập bằng mật khẩu
        if user.is_social_user:
            raise serializers.ValidationError(
                "Tài khoản mạng xã hội không thể đăng nhập bằng mật khẩu")

        data['user'] = user
        return data


class RefreshTokenSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Mật khẩu cũ không chính xác')
        return value

    def validate_new_password(self, value):
        try:
            validate_password(value, self.context['request'].user)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Mật khẩu mới không trùng khớp'
            })
        return data


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        self.refresh_token = attrs['refresh']
        return attrs


class SocialLoginSerializer(serializers.Serializer):
    provider = serializers.ChoiceField(choices=[('google', 'Google'), ('facebook', 'Facebook')])
    access_token = serializers.CharField(required=True)
