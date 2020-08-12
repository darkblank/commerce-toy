from rest_framework import serializers

from product.models import Product, ProductOption
from user.serializers import ProviderSerializer


class ProductOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductOption
        fields = (
            'id', 'stock', 'name',
        )


class ProductSerializer(serializers.ModelSerializer):
    provider = ProviderSerializer()
    options = ProductOptionSerializer(many=True)

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'price', 'shipping_price',
            'is_on_sale', 'can_bundle', 'created_at', 'updated_at', 'provider', 'options',
        )


class ProductWithoutOptionsSerializer(ProductSerializer):
    class Meta:
        model = Product
        fields = (
            'id', 'name', 'price', 'shipping_price',
            'is_on_sale', 'can_bundle', 'created_at', 'updated_at', 'provider',
        )


class ProductOptionWithProductSerializer(ProductOptionSerializer):
    product = ProductWithoutOptionsSerializer()

    class Meta:
        model = ProductOption
        fields = (
            'id', 'stock', 'name', 'product',
        )
