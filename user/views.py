# Create your views here.
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny

from user.serializers import UserSerializer


class UserCreateAPIView(CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer
