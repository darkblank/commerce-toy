from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from user.models import Provider

User = get_user_model()


class ToyTestCase(APITestCase):
    def create_normal_user(self):
        return User.objects.create_user(
            username='darkblank',
            password='toyproject12!@',
            name='김승준',
            email='darkblank1990@gmail.com',
            phone_number='01034935259',
        )

    def create_provider(self, username, name, phone_number, email):
        user = User.objects.create_user(
            username=username,
            password='toyproject12!@',
            name=name,
            email=email,
            phone_number=phone_number,
        )

        return Provider.objects.create(
            user=user,
            provider_name=name,
        )
