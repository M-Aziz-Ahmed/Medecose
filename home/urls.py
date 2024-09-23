from django.urls import path
from .views import home, register, verify_email, contact, success, product, cart, add_to_cart, remove_from_cart, cod, confirm_order, search_view, user_orders, CustomLoginView

urlpatterns = [
    path('', home, name='home'),
    path('register/', register, name='register'),
    path('verify_email/', verify_email, name='verify_email'),
    path('contact/', contact, name='contact'),
    path('success/', success, name='success'),
    path('product/<int:post_id>/', product, name='product'),
    path('cart/', cart, name='cart'),
    path('add_to_cart/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('remove_from_cart/<int:product_id>/', remove_from_cart, name='remove_from_cart'),
    path('cod/', cod, name='cod'),
    path('confirm_order/', confirm_order, name='confirm_order'),
    path('search/', search_view, name='search'),
    path('user_orders/', user_orders, name='user_orders'),
    path('login/', CustomLoginView.as_view(), name='login'),
]
