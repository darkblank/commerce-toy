from rest_framework.test import APIClient

from common.tests import ToyTestCase
from product.models import Product, ProductOption


class TestProductListAPIViewGET(ToyTestCase):
    api_url = '/products'

    def setUp(self):
        self.client = APIClient()
        self.provider1 = self.create_provider(
            username='Ably',
            name='Ably',
            phone_number='01033333333',
            email='ddd@naver.com',
        )

        self.product1 = Product.objects.create(
            provider=self.provider1,
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
            provider=self.provider1,
            name='product2',
            price=3000,
            shipping_price=3000,
            is_on_sale=False,
            can_bundle=True,
        )
        self.product2_option = ProductOption.objects.create(
            product=self.product2,
            stock=10,
            name='anything'
        )

        self.product3 = Product.objects.create(
            provider=self.provider1,
            name='product3',
            price=3000,
            shipping_price=0,
            is_on_sale=True,
            can_bundle=True,
        )
        self.product3_option = ProductOption.objects.create(
            product=self.product3,
            stock=10,
            name='anything'
        )

        self.product4 = Product.objects.create(
            provider=self.provider1,
            name='product4',
            price=3000,
            shipping_price=3000,
            is_on_sale=False,
            can_bundle=True,
        )
        self.product4_option = ProductOption.objects.create(
            product=self.product4,
            stock=10,
            name='anything'
        )

    def test_쿼리_파라미터를_따로_사용하지_않고_모든_상품_리스트_노출_200_성공(self):
        response = self.client.get(self.api_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], Product.objects.count())
        self.assertEqual(
            set(response.json()['results'][0]),
            {
                'id', 'name', 'price', 'shipping_price',
                'is_on_sale', 'can_bundle', 'created_at', 'updated_at', 'provider', 'options',
            }
        )
