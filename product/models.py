from django.contrib.gis.db import models

from common.models import TimeStampModel
from user.models import Provider


class Product(TimeStampModel):
    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name='products',
    )
    name = models.CharField(
        unique=True,
        max_length=50
    )
    price = models.PositiveIntegerField()
    shipping_price = models.PositiveIntegerField(
        default=0
    )
    is_on_sale = models.BooleanField(
        default=True
    )
    can_bundle = models.BooleanField(
        default=True
    )

    class Meta:
        db_table = 'product'
        verbose_name = '상품'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class ProductOption(models.Model):
    product = models.ForeignKey(
        Product,
        related_name='options',
        on_delete=models.CASCADE,
    )
    stock = models.PositiveIntegerField(
        default=0,
    )
    name = models.CharField(
        max_length=50,
    )

    class Meta:
        db_table = 'product_option'
        verbose_name = '상품옵션'
        verbose_name_plural = verbose_name
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'name'],
                name='unique option for each product'
            )
        ]
