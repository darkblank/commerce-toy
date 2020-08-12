import json

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient

User = get_user_model()


class TestUserCreateAPIViewPOST(APITestCase):
    api_url = '/users'

    def setUp(self):
        self.client = APIClient()

    def test_사용자가_회원가입_할_때_필요한_정보들을_제대로_입력하면_회원가입_201_성공(self):
        user_count_query = User.objects.all()
        user_count_before_user_created = user_count_query.count()

        response = self.client.post(
            path=self.api_url,
            content_type='application/json',
            data=json.dumps({
                'username': 'darkblank',
                'name': '김승준',
                'email': 'darkblank1990@gmail.com',
                'phone_number': '01034935259',
                'password': 'toyproject12!@',
                'password2': 'toyproject12!@'
            })
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(user_count_query.count(), user_count_before_user_created + 1)
        self.assertEqual(
            set(response.json()),
            {
                'id', 'username', 'name', 'email', 'phone_number',
                'is_active', 'is_staff', 'created_at', 'updated_at',
            }
        )

    def test_사용자가_회원가입_할_때_필요한_정보들을_입력하지_않으면_회원가입_400_에러(self):
        user_count_query = User.objects.all()
        user_count_before_user_created = user_count_query.count()

        response = self.client.post(
            path=self.api_url,
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(user_count_query.count(), user_count_before_user_created + 0)
        self.assertEqual(
            response.json(),
            {
                'username': ['이 필드는 필수 항목입니다.'],
                'name': ['이 필드는 필수 항목입니다.'],
                'password': ['이 필드는 필수 항목입니다.'],
                'password2': ['이 필드는 필수 항목입니다.'],
                'email': ['이 필드는 필수 항목입니다.'],
                'phone_number': ['이 필드는 필수 항목입니다.']
            }
        )

    def test_사용자가_회원가입_할_때_비밀번호_형식이_틀리면_400_에러(self):
        user_count_query = User.objects.all()
        user_count_before_user_created = user_count_query.count()

        response = self.client.post(
            path=self.api_url,
            content_type='application/json',
            data=json.dumps({
                'username': 'darkblank',
                'name': '김승준',
                'email': 'darkblank1990@gmail.com',
                'phone_number': '01034935259',
                'password': 'toyproject12',
                'password2': 'toyproject12'
            })
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(user_count_query.count(), user_count_before_user_created + 0)
        self.assertEqual(
            response.json(),
            {'password': ['8글자 이상 16글자 이하, 최소 하나씩의 문자/숫자/특수문자가 포함되어야 합니다.'],
             'password2': ['8글자 이상 16글자 이하, 최소 하나씩의 문자/숫자/특수문자가 포함되어야 합니다.']}
        )

    def test_사용자가_회원가입_할_때_username_형식이_틀리면_400_에러(self):
        user_count_query = User.objects.all()
        user_count_before_user_created = user_count_query.count()

        response = self.client.post(
            path=self.api_url,
            content_type='application/json',
            data=json.dumps({
                'username': 'darkblank!@',
                'name': '김승준',
                'email': 'darkblank1990@gmail.com',
                'phone_number': '01034935259',
                'password': 'toyproject12!@',
                'password2': 'toyproject12!@'
            })
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(user_count_query.count(), user_count_before_user_created + 0)
        self.assertEqual(
            response.json(),
            {'username': ['username은 영문 숫자 및 .-_ 의 특수문자만 사용 가능하고 4글자 이상 16글자 이하여야 합니다.']}
        )

    def test_사용자가_회원가입_할_때_전화번호_형식이_틀리면_400_에러(self):
        user_count_query = User.objects.all()
        user_count_before_user_created = user_count_query.count()

        response = self.client.post(
            path=self.api_url,
            content_type='application/json',
            data=json.dumps({
                'username': 'darkblank',
                'name': '김승준',
                'email': 'darkblank1990@gmail.com',
                'phone_number': '0103-5259',
                'password': 'toyproject12!@',
                'password2': 'toyproject12!@'
            })
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(user_count_query.count(), user_count_before_user_created + 0)
        self.assertEqual(
            response.json(),
            {'phone_number': ['01000000000 의 형태로 입력 해주세요.']}
        )

    def test_사용자가_회원가입_할_때_재입력_비밀번호와_그냥_비밀번호가_다르면_400_에러(self):
        user_count_query = User.objects.all()
        user_count_before_user_created = user_count_query.count()

        response = self.client.post(
            path=self.api_url,
            content_type='application/json',
            data=json.dumps({
                'username': 'darkblank',
                'name': '김승준',
                'email': 'darkblank1990@gmail.com',
                'phone_number': '01034935259',
                'password': 'styleshare12!',
                'password2': 'styleshare12!@'
            })
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(user_count_query.count(), user_count_before_user_created + 0)
        self.assertEqual(
            response.json(),
            {'non_field_errors': ['비밀번호가 일치하지 않습니다.']}
        )
