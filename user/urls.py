from django.urls import path

from user.views import UserCreateAPIView, UserTokenObtainAPIView

urlpatterns = [
    path('', UserCreateAPIView.as_view(), name='user-create'),
    path('/token/obtain', UserTokenObtainAPIView.as_view(), name='user-token-obtain'),
]
