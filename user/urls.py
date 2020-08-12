from django.urls import path

from user.views import UserCreateAPIView

urlpatterns = [
    path('', UserCreateAPIView.as_view(), name='user-create'),
]
