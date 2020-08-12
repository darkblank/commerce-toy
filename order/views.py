from rest_framework import status
from rest_framework.generics import ListCreateAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.cache import has_obtained_redis_lock, release_redis_lock
from order.cache_keys import CART_CREATE_LOCK_USER_, ORDER_CREATE_LOCK_USER_
from order.models import Cart, Order
from order.serializers import MeCartSerializer, MeOrderSerializer


class MeCartListCreateAPIView(ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = MeCartSerializer
    queryset = Cart.objects.select_related('user', 'product_option__product__provider')

    def get_queryset(self):
        return super().get_queryset().order_by('-id')

    def filter_queryset(self, queryset):
        return super().filter_queryset(queryset).filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        lock_key = CART_CREATE_LOCK_USER_(request.user.id)

        if has_obtained_redis_lock(lock_key, 3):
            try:
                response = super().create(request, *args, **kwargs)
            finally:
                release_redis_lock(lock_key)
        else:
            response = Response('처리중입니다.', status=status.HTTP_423_LOCKED)

        return response


class MeOrderCreateAPIView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = MeOrderSerializer
    queryset = Order.objects.select_related(
        'user', 'payment',
    ).prefetch_related(
        'order_products__product_option__product__provider',
    )

    def create(self, request, *args, **kwargs):
        lock_key = ORDER_CREATE_LOCK_USER_(request.user.id)

        if has_obtained_redis_lock(lock_key, 3):
            try:
                response = super().create(request, *args, **kwargs)
            finally:
                release_redis_lock(lock_key)
        else:
            response = Response('처리중입니다.', status=status.HTTP_423_LOCKED)

        return response
