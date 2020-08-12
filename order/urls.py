from django.urls import path

from order.views import MeCartListCreateAPIView

urlpatterns = [
    path('', MeCartListCreateAPIView.as_view(), name='cart')
]