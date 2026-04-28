from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """
        Tạo regular user với email và password
        """
        if not email:
            raise ValueError('Email là bắt buộc cho regular user')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)

        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_social_user(self, provider, social_id, email=None, **extra_fields):
        """
        Tạo social user với provider và social_id
        """
        if not provider or not social_id:
            raise ValueError(
                'Provider và Social ID là bắt buộc cho social user')

        # Tạo username duy nhất từ social info
        username = f"{provider}_{social_id}"
        email = self.normalize_email(email) if email else None

        # Kiểm tra xem username đã tồn tại chưa
        if self.model.objects.filter(username=username).exists():
            raise ValueError('Username đã tồn tại cho social user này')

        user = self.model(
            username=username,
            email=email,
            provider=provider,
            social_id=social_id,
            **extra_fields
        )
        user.set_unusable_password()  # Social user không dùng password
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    # Điều chỉnh username field để phù hợp với cả regular và social user
    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        null=True,
        blank=True,
        help_text=_('Chỉ dùng cho social auth. 150 ký tự trở xuống.'),
    )

    # Email là chính (bắt buộc với regular user)
    email = models.EmailField(
        _('email address'),
        unique=True,
        null=True,  # Cho phép null cho social user
        blank=True,
        error_messages={
            'unique': _("Email đã được sử dụng."),
        }
    )

    # Cho phép password null cho social user
    password = models.CharField(
        _('password'),
        max_length=128,
        null=True,
        blank=True
    )

    # Thông tin cá nhân
    full_name = models.CharField(_('full name'), max_length=100, blank=True)
    phone = models.CharField(_('phone number'), max_length=20, blank=True)
    address = models.CharField(_('address'), max_length=255, blank=True)
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="ticket_movie_user_groups",
        related_query_name="ticket_movie_user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="ticket_movie_user_permissions",
        related_query_name="ticket_movie_user",
    )

    # Phân quyền
    class Role(models.TextChoices):
        CUSTOMER = 'customer', _('Customer')
        STAFF = 'staff', _('Staff')
        ADMIN = 'admin', _('Admin')

    role = models.CharField(
        _('role'),
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER
    )

    # Social auth fields
    provider = models.CharField(max_length=50, blank=True, null=True)
    social_id = models.CharField(max_length=200, blank=True, null=True)
    avatar = models.URLField(blank=True, null=True)

    # Sử dụng email làm USERNAME_FIELD
    USERNAME_FIELD = 'email'
    # Thêm các trường bắt buộc khi tạo superuser
    REQUIRED_FIELDS = ['full_name']

    objects = UserManager()

    class Meta:
        db_table = 'users'
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return self.email or f"{self.provider}:{self.social_id}"

    def clean(self):
        super().clean()
        # Kiểm tra xem user có email hoặc là social user không
        if not self.email and not (self.provider and self.social_id):
            raise ValidationError(
                'User must have either email or social credentials')

    def save(self, *args, **kwargs):
        # Validate password nếu có thay đổi và là regular user
        if not self.is_social_user and self.password and not self.check_password(self.password):
            try:
                validate_password(self.password)
            except ValidationError as e:
                raise ValidationError({'password': e.messages})

        self.clean()
        super().save(*args, **kwargs)

    @property
    def is_social_user(self):
        """Kiểm tra có phải là social user không"""
        return bool(self.provider and self.social_id)

    @property
    def is_staff_member(self):
        """Kiểm tra user có phải là staff hoặc admin không"""
        return self.role in [self.Role.STAFF, self.Role.ADMIN] or self.is_staff

    @property
    def is_admin(self):
        """Kiểm tra user có phải là admin không"""
        return self.role == self.Role.ADMIN or self.is_superuser

    def get_username(self):
        """Lấy username để hiển thị (dùng cho social user)"""
        return self.username if self.is_social_user else self.email

    @property
    def get_user_id(self):
        return self.id
    
class ThemeSetting(models.Model):

    key = models.CharField(max_length=50)
    value = models.CharField(max_length=20)  # hex color

    def __str__(self):
        return f"{self.key}"