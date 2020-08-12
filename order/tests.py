import json

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from common.cache import has_obtained_redis_lock, release_redis_lock
from common.tests import ToyTestCase
from order.cache_keys import CART_CREATE_LOCK_USER_, ORDER_CREATE_LOCK_USER_
from order.models import Cart, OrderProduct, Payment, Order
from product.models import Product, ProductOption

User = get_user_model()


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


class TestMeCartListCreateAPIViewGET(ToyTestCase):
    api_url = '/users/me/carts'

    def setUp(self):
        self.client = APIClient()
        self.me = self.create_normal_user()
        self.another_user = User.objects.create_user(
            username='another_user',
            password='toyproject12!@',
            name='아무나',
            email='anybody@any.body',
            phone_number='01012344321',
        )

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

        self.me_cart_option1 = Cart.objects.create(
            user=self.me,
            product_option=self.product1_option,
            quantity=1
        )
        self.me_cart_option2 = Cart.objects.create(
            user=self.me,
            product_option=self.product2_option,
            quantity=1,
        )

        self.another_user_cart_option1 = Cart.objects.create(
            user=self.another_user,
            product_option=self.product1_option,
            quantity=1
        )
        self.another_user_cart_option2 = Cart.objects.create(
            user=self.another_user,
            product_option=self.product2_option,
            quantity=1
        )

    def test_로그인한_사용자가_본인_장바구니_리스트를_보면_다른_사용자의_장바구니_리스트는_나오지_않고_200_성공(self):
        self.client.force_authenticate(user=self.me)
        response = self.client.get(path=self.api_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], Cart.objects.filter(user=self.me).count())
        self.assertEqual(
            set(response.json()['results'][0]),
            {'id', 'user_id', 'quantity', 'product_option'}
        )
        self.assertEqual(
            set(response.json()['results'][0]['product_option']),
            {'id', 'stock', 'name', 'product'}
        )
        self.assertEqual(
            set(response.json()['results'][0]['product_option']['product']),
            {
                'id', 'name', 'price', 'shipping_price',
                'is_on_sale', 'can_bundle', 'created_at', 'updated_at', 'provider',
            }
        )

    def test_로그인하지_않은_사용자가_장바구니_리스트를_확인하려고_할_시_401_에러(self):
        response = self.client.get(path=self.api_url)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {'detail': '자격 인증데이터(authentication credentials)가 제공되지 않았습니다.'})


class TestMeOrderCreateAPIViewPOST(ToyTestCase):
    api_url = '/users/me/orders'

    def setUp(self):
        self.client = APIClient()
        self.me = self.create_normal_user()
        self.provider1 = self.create_provider(
            username='Ably',
            name='Ably',
            phone_number='01033333333',
            email='ddd@naver.com',
        )
        self.provider2 = self.create_provider(
            username='zigzag',
            name='셀럽입점사',
            phone_number='01033334444',
            email='aaa@naver.com',
        )

        self.product1 = Product.objects.create(
            provider=self.provider1,
            name='product1',
            price=3000,
            shipping_price=2000,
            is_on_sale=True,
            can_bundle=True,
        )
        self.product1_option1 = ProductOption.objects.create(
            product=self.product1,
            stock=10,
            name='anything',
        )

        self.product2 = Product.objects.create(
            provider=self.provider1,
            name='product2',
            price=3000,
            shipping_price=3000,
            is_on_sale=True,
            can_bundle=True,
        )
        self.product2_option1 = ProductOption.objects.create(
            product=self.product2,
            stock=10,
            name='anything',
        )

        self.product3 = Product.objects.create(
            provider=self.provider2,
            name='product3',
            price=3000,
            shipping_price=2000,
            is_on_sale=True,
            can_bundle=True,
        )
        self.product3_option1 = ProductOption.objects.create(
            product=self.product3,
            stock=10,
            name='anything',
        )

        self.product4 = Product.objects.create(
            provider=self.provider2,
            name='product4',
            price=3000,
            shipping_price=2000,
            is_on_sale=True,
            can_bundle=False,
        )
        self.product4_option1 = ProductOption.objects.create(
            product=self.product4,
            stock=10,
            name='anything',
        )

        self.me_cart_option1 = Cart.objects.create(
            user=self.me,
            product_option=self.product1_option1,
            quantity=1,
        )
        self.me_cart_option2 = Cart.objects.create(
            user=self.me,
            product_option=self.product2_option1,
            quantity=5,
        )
        self.me_cart_option3 = Cart.objects.create(
            user=self.me,
            product_option=self.product3_option1,
            quantity=5,
        )
        self.me_cart_option4 = Cart.objects.create(
            user=self.me,
            product_option=self.product4_option1,
            quantity=5,
        )

    def test_로그인한_사용자가_본인_장바구니에_있는_상품옵션들을_주문하려고_할_때_재고가_있으면_주문_201_성공(self):
        order_count_query = Order.objects.filter(user=self.me)
        order_product_count_query = OrderProduct.objects.filter(user=self.me)
        payment_count_query = Payment.objects.filter(order__user=self.me)
        order_count_before_order_create = order_count_query.count()
        order_product_count_before_order_create = order_product_count_query.count()
        payment_count_before_order_create = payment_count_query.count()
        cart_ids_to_order = [
            self.me_cart_option1.id, self.me_cart_option2.id, self.me_cart_option3.id, self.me_cart_option4.id
        ]

        self.client.force_authenticate(user=self.me)
        response = self.client.post(
            path=self.api_url,
            content_type='application/json',
            data=json.dumps({
                'cart_ids': cart_ids_to_order,
                'shipping_address': '서울시 동작구 아무곳이나',
                'shipping_request_note': '경비실에 맡겨주세요',
                'pay_method': 'CARD',
            })
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(order_count_query.count(), order_count_before_order_create + 1)
        self.assertEqual(
            order_product_count_query.count(),
            order_product_count_before_order_create + len(cart_ids_to_order)
        )
        self.assertEqual(payment_count_query.count(), payment_count_before_order_create + 1)
        self.assertEqual(
            set(response.json()),
            {
                'id', 'order_uid', 'shipping_price', 'shipping_address', 'shipping_request_note',
                'created_at', 'updated_at', 'is_paid', 'user', 'order_products', 'payment',
            }
        )
        final_shipping_price = (
                min(
                    self.me_cart_option1.product_option.product.shipping_price,
                    self.me_cart_option2.product_option.product.shipping_price
                )
                + self.me_cart_option3.product_option.product.shipping_price
                + self.me_cart_option4.product_option.product.shipping_price
        )

        self.assertEqual(
            response.json()['shipping_price'],
            final_shipping_price,
        )
        self.assertEqual(
            response.json()['payment']['pay_price'],
            (self.me_cart_option1.quantity * self.me_cart_option1.product_option.product.price)
            + (self.me_cart_option2.quantity * self.me_cart_option2.product_option.product.price)
            + (self.me_cart_option3.quantity * self.me_cart_option3.product_option.product.price)
            + (self.me_cart_option4.quantity * self.me_cart_option4.product_option.product.price)
            + final_shipping_price
        )

    def test_로그인한_사용자가_본인_장바구니에_있는_상품옵션들을_주문하려고_할_때_재고가_있으면_주문을_여러번_해도_201_성공(self):
        cart_ids_to_order = [
            self.me_cart_option1.id, self.me_cart_option2.id, self.me_cart_option3.id, self.me_cart_option4.id
        ]

        self.client.force_authenticate(user=self.me)
        self.client.post(
            path=self.api_url,
            content_type='application/json',
            data=json.dumps({
                'cart_ids': cart_ids_to_order,
                'shipping_address': '서울시 동작구 아무곳이나',
                'shipping_request_note': '경비실에 맡겨주세요',
                'pay_method': 'CARD',
            })
        )
        order_count_query = Order.objects.filter(user=self.me)
        order_product_count_query = OrderProduct.objects.filter(user=self.me)
        payment_count_query = Payment.objects.filter(order__user=self.me)
        order_count_before_order_create = order_count_query.count()
        order_product_count_before_order_create = order_product_count_query.count()
        payment_count_before_order_create = payment_count_query.count()

        response = self.client.post(
            path=self.api_url,
            content_type='application/json',
            data=json.dumps({
                'cart_ids': cart_ids_to_order,
                'shipping_address': '서울시 동작구 아무곳이나',
                'shipping_request_note': '경비실에 맡겨주세요',
                'pay_method': 'CARD',
            })
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(order_count_query.count(), order_count_before_order_create + 1)
        self.assertEqual(
            order_product_count_query.count(),
            order_product_count_before_order_create + len(cart_ids_to_order)
        )
        self.assertEqual(payment_count_query.count(), payment_count_before_order_create + 1)
        self.assertEqual(
            set(response.json()),
            {
                'id', 'order_uid', 'shipping_price', 'shipping_address', 'shipping_request_note',
                'created_at', 'updated_at', 'is_paid', 'user', 'order_products', 'payment',
            }
        )
        final_shipping_price = (
                min(
                    self.me_cart_option1.product_option.product.shipping_price,
                    self.me_cart_option2.product_option.product.shipping_price
                )
                + self.me_cart_option3.product_option.product.shipping_price
                + self.me_cart_option4.product_option.product.shipping_price
        )

        self.assertEqual(
            response.json()['shipping_price'],
            final_shipping_price,
        )
        self.assertEqual(
            response.json()['payment']['pay_price'],
            (self.me_cart_option1.quantity * self.me_cart_option1.product_option.product.price)
            + (self.me_cart_option2.quantity * self.me_cart_option2.product_option.product.price)
            + (self.me_cart_option3.quantity * self.me_cart_option3.product_option.product.price)
            + (self.me_cart_option4.quantity * self.me_cart_option4.product_option.product.price)
            + final_shipping_price
        )

    def test_로그인하지_않은_사용자가_본인_장바구니에_있는_상품옵션들을_주문하려고_할_때_401_에러(self):
        order_count_query = Order.objects.filter(user=self.me)
        order_product_count_query = OrderProduct.objects.filter(user=self.me)
        payment_count_query = Payment.objects.filter(order__user=self.me)
        order_count_before_order_create = order_count_query.count()
        order_product_count_before_order_create = order_product_count_query.count()
        payment_count_before_order_create = payment_count_query.count()
        cart_ids_to_order = [
            self.me_cart_option1.id, self.me_cart_option2.id, self.me_cart_option3.id, self.me_cart_option4.id
        ]

        response = self.client.post(
            path=self.api_url,
            content_type='application/json',
            data=json.dumps({
                'cart_ids': cart_ids_to_order,
                'shipping_address': '서울시 동작구 아무곳이나',
                'shipping_request_note': '경비실에 맡겨주세요',
                'pay_method': 'CARD',
            })
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(order_count_query.count(), order_count_before_order_create + 0)
        self.assertEqual(order_product_count_query.count(), order_product_count_before_order_create + 0)
        self.assertEqual(payment_count_query.count(), payment_count_before_order_create + 0)
        self.assertEqual(response.json(), {'detail': '자격 인증데이터(authentication credentials)가 제공되지 않았습니다.'})

    def test_로그인한_사용자가_본인_장바구니에_있는_상품옵션들을_주문하려고_할_때_Required_Field를_Request_Body로_보내지_않으면_400_에러(self):
        order_count_query = Order.objects.filter(user=self.me)
        order_product_count_query = OrderProduct.objects.filter(user=self.me)
        payment_count_query = Payment.objects.filter(order__user=self.me)
        order_count_before_order_create = order_count_query.count()
        order_product_count_before_order_create = order_product_count_query.count()
        payment_count_before_order_create = payment_count_query.count()

        self.client.force_authenticate(user=self.me)
        response = self.client.post(
            path=self.api_url,
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(order_count_query.count(), order_count_before_order_create + 0)
        self.assertEqual(order_product_count_query.count(), order_product_count_before_order_create + 0)
        self.assertEqual(payment_count_query.count(), payment_count_before_order_create + 0)
        self.assertEqual(
            response.json(),
            {
                'shipping_address': ['이 필드는 필수 항목입니다.'],
                'cart_ids': ['이 필드는 필수 항목입니다.'],
                'pay_method': ['이 필드는 필수 항목입니다.']
            }
        )

    def test_로그인한_사용자가_본인_장바구니에_없는_상품옵션을_주문하려고하면_400_에러(self):
        order_count_query = Order.objects.filter(user=self.me)
        order_product_count_query = OrderProduct.objects.filter(user=self.me)
        payment_count_query = Payment.objects.filter(order__user=self.me)
        order_count_before_order_create = order_count_query.count()
        order_product_count_before_order_create = order_product_count_query.count()
        payment_count_before_order_create = payment_count_query.count()
        cart_ids_to_order = [
            3000, 4000, 5000
        ]

        self.client.force_authenticate(user=self.me)
        response = self.client.post(
            path=self.api_url,
            content_type='application/json',
            data=json.dumps({
                'cart_ids': cart_ids_to_order,
                'shipping_address': '서울시 동작구 아무곳이나',
                'shipping_request_note': '경비실에 맡겨주세요',
                'pay_method': 'CARD',
            })
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(order_count_query.count(), order_count_before_order_create + 0)
        self.assertEqual(order_product_count_query.count(), order_product_count_before_order_create + 0)
        self.assertEqual(payment_count_query.count(), payment_count_before_order_create + 0)
        self.assertEqual(response.json(), {'cart_ids': ['잘못된 cart id가 포함되어 있습니다.']})

    def test_로그인한_사용자가_본인_장바구니에_있는_상품옵션을_주문하려고_할_때_허용되지_않은_결제수단을_사용하면_400_에러(self):
        order_count_query = Order.objects.filter(user=self.me)
        order_product_count_query = OrderProduct.objects.filter(user=self.me)
        payment_count_query = Payment.objects.filter(order__user=self.me)
        order_count_before_order_create = order_count_query.count()
        order_product_count_before_order_create = order_product_count_query.count()
        payment_count_before_order_create = payment_count_query.count()
        cart_ids_to_order = [
            self.me_cart_option1.id, self.me_cart_option2.id, self.me_cart_option3.id, self.me_cart_option4.id
        ]

        self.client.force_authenticate(user=self.me)
        response = self.client.post(
            path=self.api_url,
            content_type='application/json',
            data=json.dumps({
                'cart_ids': cart_ids_to_order,
                'shipping_address': '서울시 동작구 아무곳이나',
                'shipping_request_note': '경비실에 맡겨주세요',
                'pay_method': 'not_allowed_pay_method',
            })
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(order_count_query.count(), order_count_before_order_create + 0)
        self.assertEqual(order_product_count_query.count(), order_product_count_before_order_create + 0)
        self.assertEqual(payment_count_query.count(), payment_count_before_order_create + 0)
        self.assertEqual(response.json(), {'pay_method': ['올바른 pay_method를 입력 해주세요.']})

    def test_로그인한_사용자가_본인_장바구니에_있는_상품옵션들을_주문하려고_할_때_재고가_없으면_주문_400_에러(self):
        order_count_query = Order.objects.filter(user=self.me)
        order_product_count_query = OrderProduct.objects.filter(user=self.me)
        payment_count_query = Payment.objects.filter(order__user=self.me)
        order_count_before_order_create = order_count_query.count()
        order_product_count_before_order_create = order_product_count_query.count()
        payment_count_before_order_create = payment_count_query.count()
        self.product1_option1.stock = 0
        self.product1_option1.save()
        self.product2_option1.stock = 0
        self.product2_option1.save()
        self.product3_option1.stock = 0
        self.product3_option1.save()
        self.product4_option1.stock = 0
        self.product4_option1.save()

        cart_ids_to_order = [
            self.me_cart_option1.id, self.me_cart_option2.id, self.me_cart_option3.id, self.me_cart_option4.id
        ]

        self.client.force_authenticate(user=self.me)
        response = self.client.post(
            path=self.api_url,
            content_type='application/json',
            data=json.dumps({
                'cart_ids': cart_ids_to_order,
                'shipping_address': '서울시 동작구 아무곳이나',
                'shipping_request_note': '경비실에 맡겨주세요',
                'pay_method': 'CARD',
            })
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(order_count_query.count(), order_count_before_order_create + 0)
        self.assertEqual(order_product_count_query.count(), order_product_count_before_order_create + 0)
        self.assertEqual(payment_count_query.count(), payment_count_before_order_create + 0)
        self.assertEqual(
            response.json(),
            {
                'non_field_errors': [
                    'product1/anything, product2/anything, product3/anything, product4/anything 의 재고가 부족합니다'
                ]
            }
        )

    def test_로그인한_사용자가_본인_장바구니에_있는_상품옵션을_주문할_때_다른_사용자_주문의_레디스_락과_상관없이_201_성공(self):
        order_count_query = Order.objects.filter(user=self.me)
        order_product_count_query = OrderProduct.objects.filter(user=self.me)
        payment_count_query = Payment.objects.filter(order__user=self.me)
        order_count_before_order_create = order_count_query.count()
        order_product_count_before_order_create = order_product_count_query.count()
        payment_count_before_order_create = payment_count_query.count()
        cart_ids_to_order = [
            self.me_cart_option1.id, self.me_cart_option2.id, self.me_cart_option3.id, self.me_cart_option4.id
        ]

        lock_key = ORDER_CREATE_LOCK_USER_('any_user_id')
        has_obtained_redis_lock(lock_key, 5)
        self.client.force_authenticate(user=self.me)
        response = self.client.post(
            path=self.api_url,
            content_type='application/json',
            data=json.dumps({
                'cart_ids': cart_ids_to_order,
                'shipping_address': '서울시 동작구 아무곳이나',
                'shipping_request_note': '경비실에 맡겨주세요',
                'pay_method': 'CARD',
            })
        )
        release_redis_lock(lock_key)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(order_count_query.count(), order_count_before_order_create + 1)
        self.assertEqual(
            order_product_count_query.count(),
            order_product_count_before_order_create + len(cart_ids_to_order)
        )
        self.assertEqual(payment_count_query.count(), payment_count_before_order_create + 1)
        self.assertEqual(
            set(response.json()),
            {
                'id', 'order_uid', 'shipping_price', 'shipping_address', 'shipping_request_note',
                'created_at', 'updated_at', 'is_paid', 'user', 'order_products', 'payment',
            }
        )
        final_shipping_price = (
                min(
                    self.me_cart_option1.product_option.product.shipping_price,
                    self.me_cart_option2.product_option.product.shipping_price
                )
                + self.me_cart_option3.product_option.product.shipping_price
                + self.me_cart_option4.product_option.product.shipping_price
        )

        self.assertEqual(
            response.json()['shipping_price'],
            final_shipping_price,
        )
        self.assertEqual(
            response.json()['payment']['pay_price'],
            (self.me_cart_option1.quantity * self.me_cart_option1.product_option.product.price)
            + (self.me_cart_option2.quantity * self.me_cart_option2.product_option.product.price)
            + (self.me_cart_option3.quantity * self.me_cart_option3.product_option.product.price)
            + (self.me_cart_option4.quantity * self.me_cart_option4.product_option.product.price)
            + final_shipping_price
        )

    def test_로그인한_사용자가_본인_장바구니에_있는_상품옵션을_주문하려고_할_때_중복_요청으로_이미_프로세스가_진행중인_경우_423_에러(self):
        order_count_query = Order.objects.filter(user=self.me)
        order_product_count_query = OrderProduct.objects.filter(user=self.me)
        payment_count_query = Payment.objects.filter(order__user=self.me)
        order_count_before_order_create = order_count_query.count()
        order_product_count_before_order_create = order_product_count_query.count()
        payment_count_before_order_create = payment_count_query.count()
        cart_ids_to_order = [
            self.me_cart_option1.id, self.me_cart_option2.id, self.me_cart_option3.id, self.me_cart_option4.id
        ]

        lock_key = ORDER_CREATE_LOCK_USER_(self.me.id)
        has_obtained_redis_lock(lock_key, 5)
        self.client.force_authenticate(user=self.me)
        response = self.client.post(
            path=self.api_url,
            content_type='application/json',
            data=json.dumps({
                'cart_ids': cart_ids_to_order,
                'shipping_address': '서울시 동작구 아무곳이나',
                'shipping_request_note': '경비실에 맡겨주세요',
                'pay_method': 'not_allowed_pay_method',
            })
        )
        release_redis_lock(lock_key)

        self.assertEqual(response.status_code, 423)
        self.assertEqual(response.json(), '처리중입니다.')
        self.assertEqual(order_count_query.count(), order_count_before_order_create + 0)
        self.assertEqual(order_product_count_query.count(), order_product_count_before_order_create + 0)
        self.assertEqual(payment_count_query.count(), payment_count_before_order_create + 0)
