# Create your views here.
from django.utils import timezone
from rest_framework import status
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from user.serializers import UserSerializer, UserTokenObtainSerializer


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
        token = serializer.get_token(user)

        user.last_login = timezone.now()
        user.save(update_fields=('last_login',))

        return Response(token, status=status.HTTP_200_OK)


