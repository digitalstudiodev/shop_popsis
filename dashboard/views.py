from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect, render
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from core.models import Order, Item, Coupon, Category, Payment
from django.contrib import messages
from users.models import User
from users.forms import UserUpdateForm, ProfileUpdateForm
from datetime import date
from user_visit.models import UserVisit

@login_required(login_url='users:login')
def dashboard(request):
    orders = Order.objects.all()
    items = Item.objects.all()
    coupons = Coupon.objects.all()
    categories = Category.objects.all()
    payments = Payment.objects.all()
    # new users and all users
    todays_date = date.today()
    all_users = User.objects.all()
    new_users = []
    for user in all_users:
        if todays_date.month == user.date_joined.date().month:
            new_users.append(user)
    # traffic
    user_visits = UserVisit.objects.all()
    new_visits = []
    for visit in user_visits:
        if todays_date.month == visit.timestamp.month:
            new_visits.append(visit)
    # sales
    new_payments = []
    for payment in payments:
        if todays_date.month == payment.timestamp.month:
            new_payments.append(payment)
    # performance
    new_perf = []
    overall_perf = []
    for payment in payments:
        overall_perf.append(payment.amount)
        if todays_date.month == payment.timestamp.month:
            new_perf.append(payment.amount)


    context = {
        'items': items,
        'orders': orders,
        'coupons': coupons,
        'categories': categories,
        'payments': payments,
        'newUsers': int(len(new_users)),
        'allUsers': int(len(all_users)),
        'allTraffic': int(len(user_visits)),
        'newTraffic': int(len(new_visits)),
        'allSales': int(len(payments)),
        'newSales': int(len(new_payments)),
        'totalPerformance': float(sum(overall_perf)),
        'newPerformance': float(sum(new_perf)),
    }
    return render(request, "dashboard/dashboard.html", context)

class ItemDetailView(LoginRequiredMixin, DetailView):
    template_name = "dashboard/item/item_detail.html"
    model = Item

class ItemCreateView(LoginRequiredMixin, CreateView):
    model = Item
    template_name = 'dashboard/item/item_form.html'
    fields = [
        'title', 'price', 'discount_price', 'category', 'label',
        'description', 'additional_info', 'image', 'image_sub_one',
        'image_sub_two', 'image_sub_three', 'inventory'
    ]

    def form_valid(self, form):
        item_title = str(form.instance.title)
        form.instance.slug = item_title.replace(" ", "-")
        messages.success(self.request, f'You have successfully added a new item')
        return super().form_valid(form)


class ItemUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Item
    template_name = "dashboard/item/item_form.html"
    fields = [
        'title', 'price', 'discount_price', 'category', 'label',
        'description', 'additional_info', 'image', 'image_sub_one',
        'image_sub_two', 'image_sub_three', 'inventory'
    ]

    def form_valid(self, form):
        item_title = str(form.instance.title)
        form.instance.slug = item_title.replace(" ", "-")
        messages.success(self.request, f'You have successfully updated the item')
        return super().form_valid(form)

    def test_func(self):
        item = self.get_object()
        if self.request.user.is_superuser:
            return True
        return False

class ItemDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Item
    success_url = '/dashboard/dashboard/'

    def test_func(self):
        item = self.get_object()
        if self.request.user.is_superuser:
            return True
        return False

class CouponCreateView(LoginRequiredMixin, CreateView):
    model = Coupon
    template_name = 'dashboard/coupon/coupon_form.html'
    fields = [
        'code', 'amount'
    ]

    def form_valid(self, form):
        code = str(form.instance.code)
        form.instance.code = code.replace(" ", "-")
        messages.success(self.request, f'You have successfully added a new coupon')
        return super().form_valid(form)

class CouponDetailView(DetailView):
    template_name = 'dashboard/coupon/coupon_detail.html'
    model = Coupon

class CouponUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Coupon
    template_name = 'dashboard/coupon/coupon_form.html'
    fields = [
        'code', 'amount'
    ]

    def form_valid(self, form):
        code = str(form.instance.code)
        form.instance.code = code.replace(" ", "-")
        messages.success(self.request, f'You have successfully updated the coupon')
        return super().form_valid(form)

    def test_func(self):
        item = self.get_object()
        if self.request.user.is_superuser:
            return True
        return False

class CouponDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Coupon
    template_name = 'dashboard/coupon/coupon_confirm_delete.html'
    success_url = '/dashboard/dashboard/'

    def test_func(self):
        coupon = self.get_object()
        if self.request.user.is_superuser:
            return True
        return False

class OrderDetailView(DetailView):
    model = Order
    template_name = "dashboard/order/order_detail.html"

class OrderUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Order
    template_name = "dashboard/order/order_form.html"
    fields = [ 
        'refund_granted', 'being_delievered', 'received'
    ]

    def form_valid(self, form):
        messages.success(self.request, f'You have successfully updated the item')
        super().form_valid(form)
        return redirect('dashboard:order-detail', self.get_object().id)

    def test_func(self):
        item = self.get_object()
        if self.request.user.is_superuser:
            return True
        return False
    

class CategoryDetailView(LoginRequiredMixin, DetailView):
    template_name = "dashboard/category/category_detail.html"
    model = Category

class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    template_name = 'dashboard/category/category_form.html'
    fields = [
       'category_choice', 'image'
    ]

    def form_valid(self, form):
        category = str(form.instance.category_choice)
        messages.success(self.request, f'You have successfully added a new item')
        return super().form_valid(form)

class CategoryUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Category
    template_name = "dashboard/category/category_form.html"
    fields = [
        'category_choice', 'image'
    ]

    def form_valid(self, form):
        category = str(form.instance.category_choice)
        messages.success(self.request, f'You have successfully updated the item')
        return super().form_valid(form)

    def test_func(self):
        item = self.get_object()
        if self.request.user.is_superuser:
            return True
        return False

class CategoryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Category
    template_name = "dashboard/category/category_confirm_delete.html"
    success_url = '/dashboard/dashboard/'

    def test_func(self):
        item = self.get_object()
        if self.request.user.is_superuser:
            return True
        return False

@login_required(login_url='users:login')
def profile_update(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Your account has been updated!')
            return redirect('dashboard:profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)
    
    context = {
        'u_form': u_form,
        'p_form': p_form,
    }
    return render(request, 'dashboard/profile/profile_update.html', context)

@login_required(login_url='users:login')
def profile(request):
    context = {
    }
    return render(request, 'dashboard/profile/profile.html', context)