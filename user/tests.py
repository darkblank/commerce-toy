from rest_framework.test import APITestCase


class TestUserCreateAPIViewPOST(APITestCase):
    api_url = '/users'

    def setUp(self):
        pass

    def test_사용자가_회원가입_할_때_필요한_정보들을_제대로_입력하면_회원가입_201_성공(self):
        pass

    def test_사용자가_회원가입_할_때_필요한_정보들을_입력하지_않으면_회원가입_400_에러(self):
        pass

    def test_사용자가_회원가입_할_때_비밀번호_형식이_틀리면_400_에러(self):
        pass

    def test_사용자가_회원가입_할_때_username_형식이_틀리면_400_에러(self):
        pass

    def test_사용자가_회원가입_할_때_전화번호_형식이_틀리면_400_에러(self):
        pass

    def test_사용자가_회원가입_할_때_재입력_비밀번호와_그냥_비밀번호가_다르면_400_에러(self):
        pass
