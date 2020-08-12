from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.relations import PrimaryKeyRelatedField

from order.models import Cart
from product.models import ProductOption
from product.serializers import ProductOptionWithProductSerializer


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
        if attrs['product_option'].stock < attrs['quantity']:
            raise ValidationError('해당 옵션의 재고가 부족합니다.')
        return attrs

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        instance = super().create(validated_data)
        return instance
