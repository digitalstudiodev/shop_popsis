from django.urls import path, include
from .views import (
    HomeView, 
    ShopView,
    SaleView,
    CheckoutView, 
    ItemDetailView, 
    add_to_cart,
    remove_from_cart,
    remove_single_item_from_cart,
    OrderSummaryView,
    PaymentView,
    AddCouponView,
    RequestRefundView,
    shipping_return,
    OrderDetailView,
    privacy_policy,
    terms_use,
    about_us,
    contact,
    dashboard,
    ItemCreateView,
    ItemUpdateView, 
    ItemDeleteView, 
    LimitedView,
    ExtremeSaleView, 
    new_base,
    home,
    OrderUpdateView
    )

app_name = 'core'

urlpatterns = [
    #path('', HomeView.as_view(), name='home'),
    path('', home, name='home'),
    path('shop/', home, name='shop'),
    path('last-chance/', SaleView.as_view(), name='last-chance'),
    path('limited/', LimitedView.as_view(), name='limited'),
    path('extreme-sale/', ExtremeSaleView.as_view(), name='extreme-sale'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('order-summary/', OrderSummaryView.as_view(), name='order-summary'),
    path('product/<slug>/', ItemDetailView.as_view(), name='product'),
    path('add-to-cart/<slug>/', add_to_cart, name='add-to-cart'),
    path('add-coupon/', AddCouponView.as_view(), name='add-coupon'),
    path('remove-from-cart/<slug>/', remove_from_cart, name='remove-from-cart'),
    path('remove-single-item-from-cart/<slug>/', remove_single_item_from_cart, name='remove-single-item-from-cart'),
    path('payment/', PaymentView.as_view(), name='payment'),
    path('request-refund/', RequestRefundView.as_view(), name='request-refund'),
    path('shipping-return/', shipping_return, name='shipping-return'),
    path('order/<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('privacy-policy/', privacy_policy, name='privacy-policy'),
    path('terms-use/', terms_use, name='terms-use'),
    path('about-us/', about_us, name='about-us'),
    path('contact/', contact, name='contact'),
    path('dashboard/', dashboard, name='dashboard'),
    path('item/new/', ItemCreateView.as_view(), name='item-create'),
    path('item/<int:pk>/update', ItemUpdateView.as_view(), name='item-update'),
    path('item/<int:pk>/delete', ItemDeleteView.as_view(), name='item-delete'),
    path('base/', new_base, name='base'),
    path('order/<int:pk>/update', OrderUpdateView.as_view(), name='order-update'),
]
