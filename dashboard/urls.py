from django.urls import path, include
import dashboard.views as dash_view

app_name = 'dashboard'

urlpatterns = [
    path('dashboard/', dash_view.DashboardView.as_view(), name='dashboard'),
    # inventory paths
    path('item/new/', dash_view.ItemCreateView.as_view(), name='item-create'),
    path('item/<int:pk>/', dash_view.ItemDetailView.as_view(), name='item-detail'),
    path('item/<int:pk>/update', dash_view.ItemUpdateView.as_view(), name='item-update'),
    path('item/<int:pk>/delete', dash_view.ItemDeleteView.as_view(), name='item-delete'),
    # coupon paths
    path('coupon/new/', dash_view.CouponCreateView.as_view(), name='coupon-create'),
    path('coupon/<int:pk>/', dash_view.CouponDetailView.as_view(), name='coupon-detail'),
    path('coupon/<int:pk>/update', dash_view.CouponUpdateView.as_view(), name='coupon-update'),
    path('coupon/<int:pk>/delete', dash_view.CouponDeleteView.as_view(), name='coupon-delete'),
    # order paths
    path('order/<int:pk>/', dash_view.OrderDetailView.as_view(), name='order-detail'),
    path('order/<int:pk>/update', dash_view.OrderUpdateView.as_view(), name='order-update'),
    # category paths
    path('category/new/', dash_view.CategoryCreateView.as_view(), name='category-create'),
    path('category/<int:pk>/', dash_view.CategoryDetailView.as_view(), name='category-detail'),
    path('category/<int:pk>/update', dash_view.CategoryUpdateView.as_view(), name='category-update'),
    path('category/<int:pk>/delete', dash_view.CategoryDeleteView.as_view(), name='category-delete'),
    # admin profile
    path('profile/', dash_view.profile, name='profile'),
    path('profile-update/', dash_view.profile_update, name='profile-update'),
]
