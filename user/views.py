# Create your views here.
from django.utils import timezone
from rest_framework import status
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from user.serializers import UserSerializer, UserTokenObtainSerializer, UserTokenRefreshSerializer


class UserCreateAPIView(CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer


class UserTokenObtainAPIView(GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = UserTokenObtainSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['authenticated_user']
        token_pair = serializer.get_token_pair(user)

        user.last_login = timezone.now()
        user.save(update_fields=('last_login',))

        return Response(token_pair, status=status.HTTP_200_OK)


class UserTokenRefreshAPIView(GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = UserTokenRefreshSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh = serializer.validated_data['refresh']
        access_token = serializer.get_access_token(refresh)

        user = serializer.get_user(refresh)
        user.last_login = timezone.now()
        user.save(update_fields=('last_login',))

        return Response(access_token, status=status.HTTP_200_OK)
