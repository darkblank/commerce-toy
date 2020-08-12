from django.urls import path

from user.views import UserCreateAPIView, UserTokenObtainAPIView, UserTokenRefreshAPIView

urlpatterns = [
    path('', UserCreateAPIView.as_view(), name='user-create'),
    path('/token/obtain', UserTokenObtainAPIView.as_view(), name='user-token-obtain'),
    path('/token/refresh', UserTokenRefreshAPIView.as_view(), name='user-token-refresh'),
]
