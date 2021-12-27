from django.urls import path, include
import core.views as core_views

app_name = 'core'

urlpatterns = [
    path('', core_views.home, name='home'),
    path('order-summary/', core_views.OrderSummaryView.as_view(), name='order-summary'),
    path('product/<str:slug>/', core_views.ItemDetailView.as_view(), name='product'),
    path('add-to-cart/<slug>/', core_views.add_to_cart, name='add-to-cart'),
    path('add-coupon/', core_views.AddCouponView.as_view(), name='add-coupon'),
    path('add-address/', core_views.AddAddressView.as_view(), name='add-address'),
    path('remove-from-cart/<slug>/', core_views.remove_from_cart, name='remove-from-cart'),
    path('remove-single-item-from-cart/<slug>/', core_views.remove_single_item_from_cart, name='remove-single-item-from-cart'),
    path('request-refund/', core_views.RequestRefundView.as_view(), name='request-refund'),
    path('terms-use/', core_views.terms_use, name='terms-use'),
    path('contact/', core_views.contact, name='contact'),
    path('shop/catalog/', core_views.ItemListView.as_view(), name='shop-catalog'),
    path('checkout/', core_views.create_checkout_session, name='checkout'),
    path('success/<str:ref_code>/', core_views.success, name='success'),
    path('cancelled/', core_views.cancelled, name='cancelled'),
    path('order-details/<int:pk>/', core_views.OrderDetailView.as_view(), name='order-detail'),
]
