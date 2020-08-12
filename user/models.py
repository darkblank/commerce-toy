from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, UserManager
from django.contrib.gis.db import models

from common.models import TimeStampModel


class User(
    TimeStampModel,
    AbstractBaseUser,
    PermissionsMixin
):
    username = models.CharField(
        max_length=16,
        unique=True,
    )
    name = models.CharField(
        max_length=50,
    )
    email = models.EmailField(
        unique=True,
    )
    phone_number = models.CharField(
        max_length=11,
        unique=True
    )
    is_active = models.BooleanField(
        default=True,
    )
    is_staff = models.BooleanField(
        default=False,
    )

    objects = UserManager()

    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'

    class Meta:
        db_table = 'user'
        verbose_name = '사용자'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.username}/{self.phone_number}'
