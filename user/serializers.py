import re

from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from rest_framework.exceptions import ValidationError, AuthenticationFailed
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    validation_error_messages = {
        'password': '8글자 이상 16글자 이하, 최소 하나씩의 문자/숫자/특수문자가 포함되어야 합니다.'
    }

    class Meta:
        model = User
        fields = (
            'id', 'username', 'name', 'password', 'password2',
            'email', 'phone_number', 'is_active', 'is_staff', 'created_at', 'updated_at',
        )

    def is_valid_password(self, password):
        """
        8글자 이상 16글자 이하, 최소 하나씩의 문자/숫자/특수문자가 포함되어야 합니다.
        """
        return bool(re.match(r'^.*(?=^.{8,16}$)(?=.*\d)(?=.*[a-zA-Z])(?=.*[!@#$%^&+=]).*$', password))

    def validate_password(self, password):
        if not self.is_valid_password(password):
            raise ValidationError(self.validation_error_messages['password'])
        return password

    def validate_password2(self, password2):
        if not self.is_valid_password(password2):
            raise ValidationError(self.validation_error_messages['password'])
        return password2

    def validate_username(self, username):
        if not re.match(r'^[a-zA-Z0-9._-]{4,16}$', username):
            raise ValidationError('username은 영문 숫자 및 .-_ 의 특수문자만 사용 가능하고 4글자 이상 16글자 이하여야 합니다.')
        return username

    def validate_phone_number(self, phone_number):
        if not re.match(r'^01(?:0|1|[6-9])(\d{3,4})(\d{4})$', phone_number):
            raise ValidationError('01000000000 의 형태로 입력 해주세요.')
        return phone_number

    def validate(self, attrs):
        password = attrs['password']
        password2 = attrs['password2']

        if password != password2:
            raise ValidationError('비밀번호가 일치하지 않습니다.')

        attrs['password'] = make_password(password)
        del attrs['password2']

        return attrs


class UserTokenObtainSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        authenticated_user = authenticate(
            request=self.context.get('request'),
            username=attrs['username'],
            password=attrs['password'],
        )

        if not authenticated_user or not authenticated_user.is_active:
            raise AuthenticationFailed()

        attrs['authenticated_user'] = authenticated_user
        return attrs

    def get_token_pair(self, user):
        refresh = RefreshToken.for_user(user)

        return dict(
            refresh=str(refresh),
            access=str(refresh.access_token)
        )


class UserTokenRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        try:
            refresh = RefreshToken(attrs['refresh'])
        except TokenError:
            raise AuthenticationFailed('만료되었거나 유효하지 않은 토큰 값입니다')

        if not User.objects.filter(
                id=refresh.get('user_id'),
                is_active=True,
        ).exists():
            raise AuthenticationFailed('유효하지 않은 토큰입니다')

        attrs['refresh'] = refresh
        return attrs

    def get_access_token(self, refresh):
        return dict(access=str(refresh.access_token))

    def get_user(self, refresh):
        return User.objects.get(id=refresh.get('user_id'))
