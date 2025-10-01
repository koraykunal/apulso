from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole(models.TextChoices):
    ADMIN = 'admin', 'Admin'
    INDIVIDUAL = 'individual', 'Bireysel'
    CORPORATE = 'corporate', 'Kurumsal'


class User(AbstractUser):
    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.INDIVIDUAL
    )
    phone = models.CharField(max_length=20, blank=True)
    company_name = models.CharField(max_length=100, blank=True)
    tax_number = models.CharField(max_length=20, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_corporate(self):
        return self.role == UserRole.CORPORATE

    @property
    def is_individual(self):
        return self.role == UserRole.INDIVIDUAL

    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True)
    website = models.URLField(blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=50, default='Turkey')
    postal_code = models.CharField(max_length=10, blank=True)
    notification_preferences = models.JSONField(default=dict)

    def __str__(self):
        return f"{self.user.email} - Profile"
