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
            provider=self.provider2,
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
            provider=self.provider2,
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

    def test_올바른_order_by를_쿼리_파라미터로_사용하면_해당_order_by로_정렬된_상품_리스트_노출_200_성공(self):
        order_by = 'name'
        response = self.client.get(self.api_url + f'?order_by={order_by}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], Product.objects.count())
        self.assertEqual(response.json()['results'][0]['name'], Product.objects.order_by(order_by).first().name)

        order_by = '-name'
        response = self.client.get(self.api_url + f'?order_by={order_by}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], Product.objects.count())
        self.assertEqual(response.json()['results'][0]['name'], Product.objects.order_by(order_by).first().name)

        order_by = 'id'
        response = self.client.get(self.api_url + f'?order_by={order_by}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], Product.objects.count())
        self.assertEqual(response.json()['results'][0]['name'], Product.objects.order_by(order_by).first().name)

        order_by = '-id'
        response = self.client.get(self.api_url + f'?order_by={order_by}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], Product.objects.count())
        self.assertEqual(response.json()['results'][0]['name'], Product.objects.order_by(order_by).first().name)

    def test_잘못된_order_by를_쿼리_파라미터로_사용하면_default로_설정된_최신순으로_정렬된_상품_리스트_노출_200_성공(self):
        order_by = 'error'
        response = self.client.get(self.api_url + f'?order_by={order_by}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], Product.objects.count())
        self.assertEqual(response.json()['results'][0]['name'], Product.objects.order_by('-id').first().name)

        order_by = 'hahahoho'
        response = self.client.get(self.api_url + f'?order_by={order_by}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], Product.objects.count())
        self.assertEqual(response.json()['results'][0]['name'], Product.objects.order_by('-id').first().name)

    def test_쿼리_파라미터로_is_on_sale에_t를_사용하면_판매중인_상품_리스트_노출_200_성공(self):
        is_on_sale = 't'
        response = self.client.get(self.api_url + f'?is_on_sale={is_on_sale}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], Product.objects.filter(is_on_sale=is_on_sale).count())
        self.assertEqual(
            {item['is_on_sale'] for item in response.json()['results']},
            {True}
        )

    def test_쿼리_파라미터로_is_on_sale에_f를_사용하면_판매중이_아닌_상품_리스트_노출_200_성공(self):
        is_on_sale = 'f'
        response = self.client.get(self.api_url + f'?is_on_sale={is_on_sale}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], Product.objects.filter(is_on_sale=is_on_sale).count())
        self.assertEqual(
            {item['is_on_sale'] for item in response.json()['results']},
            {False}
        )

    def test_쿼리_파라미터로_is_on_sale에_잘못된_값을_사용하면_모든_상품_리스트_노출_200_성공(self):
        is_on_sale = 'hahahoho'
        response = self.client.get(self.api_url + f'?is_on_sale={is_on_sale}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], Product.objects.count())
        self.assertEqual(
            {item['is_on_sale'] for item in response.json()['results']},
            {True, False}
        )

    def test_쿼리_파라미터로_provider_id를_사용하여_원하는_입점사의_상품_리스트만_노출_200_성공(self):
        provider_id = self.provider1.id
        response = self.client.get(self.api_url + f'?provider_id={provider_id}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], Product.objects.filter(provider_id=provider_id).count())
        self.assertEqual(
            {item['provider']['id'] for item in response.json()['results']},
            {provider_id}
        )

        provider_id = self.provider2.id
        response = self.client.get(self.api_url + f'?provider_id={provider_id}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], Product.objects.filter(provider_id=provider_id).count())
        self.assertEqual(
            {item['provider']['id'] for item in response.json()['results']},
            {provider_id}
        )

    def test_쿼리_파라미터로_int가_아닌_provider_id를_사용하면_모든_상품_리스트_노출_200_성공(self):
        provider_id = 'not_int'
        response = self.client.get(self.api_url + f'?provider_id={provider_id}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], Product.objects.count())
        self.assertEqual(
            {item['provider']['id'] for item in response.json()['results']},
            {self.provider1.id, self.provider2.id}
        )
