from django.urls import path

from product.views import ProductListAPIView

urlpatterns = [
    path('', ProductListAPIView.as_view(), name='product-list'),
]
