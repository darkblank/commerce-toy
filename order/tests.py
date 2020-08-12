import json

from rest_framework.test import APIClient

from common.tests import ToyTestCase
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
