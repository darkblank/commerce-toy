from django.contrib.auth import get_user_model
from django.contrib.gis.db import models

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
