from django.db import transaction
from django.db.models import Sum, Value, Min
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.relations import PrimaryKeyRelatedField

from order.models import Cart, OrderProduct, Payment, Order
from product.models import ProductOption, Product
from product.serializers import ProductOptionWithProductSerializer
from user.serializers import UserSerializer


class MeCartSerializer(serializers.ModelSerializer):
    product_option_id = PrimaryKeyRelatedField(
        queryset=ProductOption.objects.all(),
        write_only=True,
        source='product_option',
    )
    product_option = ProductOptionWithProductSerializer(read_only=True)

    class Meta:
        model = Cart
        fields = (
            'id', 'user_id', 'product_option_id', 'quantity',
            'product_option',
        )

    def validate(self, attrs):
        if Cart.objects.filter(
                user=self.context['request'].user,
                product_option=attrs['product_option'],
        ).exists():
            raise ValidationError('이미 장바구니에 있는 상품 옵션입니다.')

        if attrs['product_option'].stock < attrs['quantity']:
            raise ValidationError('해당 옵션의 재고가 부족합니다.')

        return attrs

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        instance = super().create(validated_data)
        return instance


class MeOrderProductSerializer(serializers.ModelSerializer):
    product_option = ProductOptionWithProductSerializer()

    class Meta:
        model = OrderProduct
        fields = (
            'id', 'product_price', 'ordered_quantity',
            'ordered_price', 'status', 'product_option',
        )

    def to_representation(self, instance):
        result = super().to_representation(instance)
        result['status'] = OrderProduct.STATUS_CHOICE[int(result['status'])]
        return result


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            'id', 'pay_price', 'pay_method', 'additional_information',
        )

    def to_representation(self, instance):
        result = super().to_representation(instance)
        result['pay_method'] = Payment.PAY_METHOD_CHOICE[int(result['pay_method'])]
        return result


class MeOrderSerializer(serializers.ModelSerializer):
    cart_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True)
    pay_method = serializers.CharField(write_only=True)

    user = UserSerializer(read_only=True)
    order_products = MeOrderProductSerializer(read_only=True, many=True)
    payment = PaymentSerializer(read_only=True)

    class Meta:
        model = Order
        fields = (
            'id', 'order_uid', 'shipping_price',
            'shipping_address', 'shipping_request_note', 'created_at', 'updated_at', 'is_paid',
            'user', 'order_products', 'payment', 'cart_ids', 'pay_method',
        )
        extra_kwargs = {
            'order_uid': {'read_only': True},
            'ordered_price': {'read_only': True},
            'refund_price': {'read_only': True},
            'shipping_price': {'read_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }

    def validate_cart_ids(self, cart_ids):
        if Cart.objects.filter(
                user=self.context['request'].user,
                id__in=cart_ids,
        ).count() != len(cart_ids):
            raise ValidationError('잘못된 cart id가 포함되어 있습니다.')
        return cart_ids

    def validate_pay_method(self, pay_method):
        if pay_method not in Payment.PAY_METHOD_CHOICE._identifier_map:
            raise ValidationError('올바른 pay_method를 입력 해주세요.')
        return pay_method

    def validate(self, attrs):
        carts = Cart.objects.filter(id__in=attrs['cart_ids']).select_related('product_option__product')

        no_stock_option_list = [
            f'{cart.product_option.product.name}/{cart.product_option.name}'
            for cart in carts if cart.quantity > cart.product_option.stock
        ]
        if no_stock_option_list:
            raise ValidationError(
                ', '.join(no_stock_option_list) + ' 의 재고가 부족합니다'
            )

        attrs['carts'] = carts
        return attrs

    def get_calculated_products_shipping_price(self, product_ids):
        return Product.objects.filter(
            id__in=product_ids, can_bundle=True
        ).values(
            'provider_id'
        ).annotate(
            min_shipping_price_group_by_provider_id=Min('shipping_price')
        ).aggregate(
            sum=Coalesce(Sum('min_shipping_price_group_by_provider_id'), Value(0))
        )['sum'] + Product.objects.filter(
            id__in=product_ids, can_bundle=False
        ).aggregate(sum=Coalesce(Sum('shipping_price'), Value(0)))['sum']

    def create_order_uid(self):
        utc_now = timezone.now()
        return f'{utc_now.year}{utc_now.month}{utc_now.day}' \
               f'{utc_now.hour}{utc_now.minute}{utc_now.second}' \
               f'{str(utc_now.microsecond)[:2]}{self.context["request"].user.id}'

    def create(self, validated_data):
        carts = validated_data['carts']
        product_ids = [cart.product_option.product_id for cart in carts]
        request_user = self.context['request'].user

        with transaction.atomic():
            order = Order.objects.create(
                user=request_user,
                order_uid=self.create_order_uid(),
                shipping_price=self.get_calculated_products_shipping_price(product_ids),
                shipping_address=validated_data['shipping_address'],
                shipping_request_note=validated_data['shipping_request_note'],
                is_paid=False,
            )

            order_products = [
                OrderProduct(
                    user=request_user,
                    cart=cart,
                    product_option=cart.product_option,
                    order=order,
                    product_price=cart.product_option.product.price,
                    ordered_quantity=cart.quantity,
                    ordered_price=cart.product_option.product.price * cart.quantity,
                    status=OrderProduct.STATUS_CHOICE.PENDING,
                ) for cart in carts
            ]
            OrderProduct.objects.bulk_create(order_products)

            Payment.objects.create(
                order=order,
                pay_price=order.shipping_price + sum([order_product.ordered_price for order_product in order_products]),
                pay_method=getattr(Payment.PAY_METHOD_CHOICE, validated_data['pay_method'])
            )

        return order
