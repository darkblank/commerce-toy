import json

from rest_framework.test import APIClient

from common.cache import has_obtained_redis_lock, release_redis_lock
from common.tests import ToyTestCase
from order.cache_keys import CART_CREATE_LOCK_USER_
from order.models import Cart
from product.models import Product, ProductOption


class TestMeCartListCreateAPIViewPOST(ToyTestCase):
    api_url = '/users/me/carts'

    def setUp(self):
        self.client = APIClient()
        self.normal_user = self.create_normal_user()
        self.provider = self.create_provider(
            username='Ably',
            name='Ably',
            phone_number='01033333333',
            email='ddd@naver.com',
        )

        self.product1 = Product.objects.create(
            provider=self.provider,
            name='product1',
            price=3000,
            shipping_price=0,
            is_on_sale=True,
            can_bundle=True,
        )
        self.product1_option = ProductOption.objects.create(
            product=self.product1,
            stock=10,
            name='anything'
        )

        self.product2 = Product.objects.create(
            provider=self.provider,
            name='product2',
            price=3000,
            shipping_price=0,
            is_on_sale=True,
            can_bundle=True,
        )

        self.product2_option = ProductOption.objects.create(
            product=self.product2,
            stock=10,
            name='anything'
        )

    def test_로그인한_사용자가_장바구니에_담으려는_상품옵션이_장바구니에_없고_재고가_있으면_장바구니에_상품옵션_추가하기_201_성공(self):
        count_query = Cart.objects.filter(user=self.normal_user)
        cart_count_before_cart_create = count_query.count()

        self.client.force_authenticate(user=self.normal_user)
        response = self.client.post(
            path=self.api_url,
            content_type='application/json',
            data=json.dumps({
                'product_option_id': self.product1_option.id,
                'quantity': 1
            })
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(count_query.count(), cart_count_before_cart_create + 1)
        self.assertEqual(
            set(response.json()),
            {'id', 'user_id', 'quantity', 'product_option'}
        )

    def test_로그인을_하지_않은_사용자가_장바구니에_상품옵션을_장바구니에_추가하려고하면_401_에러(self):
        count_query = Cart.objects.filter(user=self.normal_user)
        cart_count_before_cart_create = count_query.count()

        response = self.client.post(
            path=self.api_url,
            content_type='application/json',
            data=json.dumps({
                'product_option_id': self.product1_option.id,
                'quantity': 1
            })
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(count_query.count(), cart_count_before_cart_create + 0)
        self.assertEqual(response.json(), {'detail': '자격 인증데이터(authentication credentials)가 제공되지 않았습니다.'})

    def test_로그인한_사용자가_장바구니에_상품옵션_추가할_때_Required_Field를_Request_Body로_보내지_않으면_400_에러(self):
        count_query = Cart.objects.filter(user=self.normal_user)
        cart_count_before_cart_create = count_query.count()

        self.client.force_authenticate(user=self.normal_user)
        response = self.client.post(
            path=self.api_url,
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(count_query.count(), cart_count_before_cart_create + 0)
        self.assertEqual(
            response.json(),
            {'product_option_id': ['이 필드는 필수 항목입니다.'], 'quantity': ['이 필드는 필수 항목입니다.']}
        )

    def test_로그인한_사용자가_장바구니에_담으려는_상품옵션의_재고가_사용자가_담으려는_수량보다_적으면_장바구니에_상품옵션_추가하기_400_에러(self):
        count_query = Cart.objects.filter(user=self.normal_user)
        cart_count_before_cart_create = count_query.count()

        self.client.force_authenticate(user=self.normal_user)
        response = self.client.post(
            path=self.api_url,
            content_type='application/json',
            data=json.dumps({
                'product_option_id': self.product1_option.id,
                'quantity': 11
            })
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(count_query.count(), cart_count_before_cart_create + 0)
        self.assertEqual(response.json(), {'non_field_errors': ['해당 옵션의 재고가 부족합니다.']})

    def test_로그인한_사용자가_장바구니에_담으려는_상품옵션이_재고는_부족하지_않지만_장바구니에_이미_있으면_400_에러(self):
        option_id_to_get = self.product1_option.id
        already_exists_cart = Cart.objects.create(
            user=self.normal_user,
            product_option_id=option_id_to_get,
            quantity=1,
        )

        self.assertEqual(already_exists_cart.quantity, 1)

        count_query = Cart.objects.filter(user=self.normal_user)
        cart_count_after_cart_create = count_query.count()

        self.client.force_authenticate(user=self.normal_user)
        response = self.client.post(
            path=self.api_url,
            content_type='application/json',
            data=json.dumps({
                'product_option_id': option_id_to_get,
                'quantity': 5
            })
        )
        already_exists_cart.refresh_from_db()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(count_query.count(), cart_count_after_cart_create + 0)
        self.assertEqual(response.json(), {'non_field_errors': ['이미 장바구니에 있는 상품 옵션입니다.']})

    def test_로그인한_사용자가_장바구니에_상품옵션을_담으려할_때_잘못된_형식의_값들을_Request_Body에_포함하면_400_에러(self):
        count_query = Cart.objects.filter(user=self.normal_user)
        cart_count_before_cart_create = count_query.count()

        self.client.force_authenticate(user=self.normal_user)
        response = self.client.post(
            path=self.api_url,
            content_type='application/json',
            data=json.dumps({
                'product_option_id': "haha",
                'quantity': "hoho"
            })
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(count_query.count(), cart_count_before_cart_create + 0)
        self.assertEqual(
            response.json(),
            {'product_option_id': ['잘못된 형식입니다. pk 값 대신 str를 받았습니다.'], 'quantity': ['유효한 정수(integer)를 넣어주세요.']}
        )

    def test_로그인한_사용자가_장바구니에_담으려는_상품옵션이_존재하지_않으면_400_에러(self):
        count_query = Cart.objects.filter(user=self.normal_user)
        cart_count_before_cart_create = count_query.count()

        self.client.force_authenticate(user=self.normal_user)
        response = self.client.post(
            path=self.api_url,
            content_type='application/json',
            data=json.dumps({
                'product_option_id': 1234,
                'quantity': 1
            })
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(count_query.count(), cart_count_before_cart_create + 0)
        self.assertEqual(
            response.json(),
            {'product_option_id': ['유효하지 않은 pk "1234" - 객체가 존재하지 않습니다.']}
        )

    def test_로그인한_사용자가_장바구니에_상품을_담을_때_다른_사용자의_레디스_락과는_상관없이_201_성공(self):
        count_query = Cart.objects.filter(user=self.normal_user)
        cart_count_before_cart_create = count_query.count()

        lock_key = CART_CREATE_LOCK_USER_('anybody_id')
        has_obtained_redis_lock(lock_key, 5)
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.post(
            path=self.api_url,
            content_type='application/json',
            data=json.dumps({
                'product_option_id': self.product1_option.id,
                'quantity': 1
            })
        )
        release_redis_lock(lock_key)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(count_query.count(), cart_count_before_cart_create + 1)

    def test_로그인한_사용자가_장바구니에_상품을_담을_때_중복_요청으로_이미_프로세스가_진행중인_경우_423_에러(self):
        count_query = Cart.objects.filter(user=self.normal_user)
        cart_count_before_cart_create = count_query.count()

        lock_key = CART_CREATE_LOCK_USER_(self.normal_user.id)
        has_obtained_redis_lock(lock_key, 5)
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.post(
            path=self.api_url,
            content_type='application/json',
            data=json.dumps({
                'product_option_id': self.product1_option.id,
                'quantity': 1
            })
        )
        release_redis_lock(lock_key)

        self.assertEqual(response.status_code, 423)
        self.assertEqual(count_query.count(), cart_count_before_cart_create + 0)
        self.assertEqual(response.json(), '처리중입니다.')
