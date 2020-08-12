from django.contrib.auth import get_user_model
from django.contrib.gis.db import models
from model_utils import Choices

from common.models import TimeStampModel
from product.models import ProductOption

User = get_user_model()


class Cart(TimeStampModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='carts',
    )
    product_option = models.ForeignKey(
        ProductOption,
        on_delete=models.CASCADE,
        related_name='carts',
    )
    quantity = models.PositiveIntegerField()

    class Meta:
        db_table = 'cart'
        verbose_name = '장바구니'
        verbose_name_plural = verbose_name
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'product_option'],
                name='unique option for each user'
            )
        ]


class Order(TimeStampModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders',
    )
    order_uid = models.CharField(
        unique=True,
        max_length=30,
    )
    shipping_price = models.PositiveIntegerField(
        verbose_name='배송비',
    )
    shipping_address = models.CharField(
        max_length=200,
    )
    shipping_request_note = models.CharField(
        max_length=200,
        null=True,
        blank=True,
    )
    is_paid = models.BooleanField(
        default=False,
    )

    class Meta:
        db_table = 'order'
        verbose_name = '주문 내역'
        verbose_name_plural = verbose_name


class OrderProduct(TimeStampModel):
    STATUS_CHOICE = Choices(
        (0, 'PENDING', 'PENDING',),
        (1, 'NOT_PAID', 'NOT_PAID',),
        (2, 'PAID', 'PAID',),
        (3, 'REFUND', 'REFUND',),
        (4, 'PARTIAL_REFUND', 'PARTIAL_REFUND',),
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='order_products',
    )
    cart = models.ForeignKey(
        Cart,
        on_delete=models.SET_NULL,
        related_name='order_products',
        null=True,
        blank=True,
    )
    product_option = models.ForeignKey(
        ProductOption,
        on_delete=models.CASCADE,
        related_name='order_products',
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='order_products',
    )
    product_price = models.PositiveIntegerField(
        verbose_name='주문 당시 상품 단가',
    )
    ordered_quantity = models.PositiveIntegerField(
        verbose_name='상품 주문 수량',
    )
    ordered_price = models.PositiveIntegerField(
        verbose_name='상품 주문 총액',
    )
    status = models.PositiveSmallIntegerField(
        choices=STATUS_CHOICE,
        default=STATUS_CHOICE.PENDING,
    )

    class Meta:
        db_table = 'order_product'
        verbose_name = '상품별 주문 내역'
        verbose_name_plural = verbose_name


class Payment(TimeStampModel):
    PAY_METHOD_CHOICE = Choices(
        (0, 'CARD', 'CARD',),
        (1, 'KAKAO', 'KAKAO',),
    )
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='payment',
    )
    pay_price = models.PositiveIntegerField()
    pay_method = models.PositiveSmallIntegerField(
        choices=PAY_METHOD_CHOICE,
    )
    additional_information = models.CharField(
        max_length=250,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = 'payment'
        verbose_name = '결제 정보'
        verbose_name_plural = verbose_name
