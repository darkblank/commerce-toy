from django.db.models import Q
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from product.models import Product
from product.serializers import ProductSerializer


class ProductListAPIView(ListAPIView):
    permission_classes = (AllowAny,)
    serializer_class = ProductSerializer
    queryset = Product.objects.select_related(
        'provider'
    ).prefetch_related(
        'options'
    ).order_by(
        '-id'
    )

    def get_queryset(self):
        queryset = super().get_queryset()
        order_by = self.request.query_params.get('order_by')

        if order_by in ('id', '-id', 'name', '-name'):
            queryset = queryset.order_by(order_by)

        return queryset

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        is_on_sale = self.request.query_params.get('is_on_sale')
        provider_id = self.request.query_params.get('provider_id')
        q = Q()

        if is_on_sale in ('t', 'f'):
            q |= Q(is_on_sale=is_on_sale)

        if provider_id and provider_id.isdigit():
            q |= Q(provider_id=provider_id)

        return queryset.filter(q)
