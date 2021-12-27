from django.conf import settings as settings
from django.urls import reverse
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, get_object_or_404, redirect, render
from django.views.generic import ListView, DetailView, View,CreateView, UpdateView, DeleteView
from django.utils import timezone
from django.views.generic.base import TemplateView
from .forms import AddressForm, CouponForm, RefundForm, PaymentForm, UserUpdateForm, CategoryForm
from .models import Item, OrderItem, Order, Payment, Coupon, Refund, CategoryChoice, Address
from users.models import User, Profile
import random
import string
import stripe
from ecommerce.settings import EMAIL_HOST_USER
from django.core.mail import send_mail, EmailMultiAlternatives
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
import stripe


stripe.api_key = settings.STRIPE_SECRET_KEY

def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))

def is_valid_form(values):
    valid = True
    for field in values:
        if field == '':
            valid = False
    return valid 

def home(request):
    context = {
        'items': Item.objects.all()[:16],
        'categories': CategoryChoice.objects.all()
    }
    return render(request, "core/home.html", context)

class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            address_form = AddressForm()
            if order.shipping_address:
                address_form = AddressForm(instance=order.shipping_address)
            context = {
                'addressform': address_form,
                'couponform': CouponForm(),
                'DISPLAY_COUPON_FORM': True,
                'object': order
            }
            return render(self.request, 'core/shopping/order_summary.html', context)
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("core:home")

class ItemDetailView(DetailView):
    model = Item
    template_name = "core/shopping/product.html"


@login_required(login_url='users:login')
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False
        )
    ##Existing user order
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    ##Item inventory
    item_inventory = order_item.item.inventory

    ##If item is in user order
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            if item_inventory == order_item.quantity:
                order_item.quantity = item_inventory
                order_item.save()
                messages.info(request, "No more in stock, only " + str(item_inventory) + " unit(s) are avilable")
                return redirect("core:order-summary")
            if item_inventory >= 1:
                order_item.quantity += 1
                order_item.save()
                messages.info(request, "This item quantity was updated.")
                return redirect("core:order-summary")
            elif item_inventory == 0:
                messages.info(request, "This item is sold out.")
                return redirect("core:order-summary")
        else:
            if item_inventory >= 1:
                order.items.add(order_item)
                order_item.quantity += 1
                messages.info(request, "This item was added to your cart.")
                return redirect("core:order-summary")
            elif item_inventory == 0:
                messages.info(request, "This item is sold out.")
                return redirect("core:product", slug=slug)
    ##If item is not in user order
    else:
        if item_inventory >= 1:
            ordered_date = timezone.now()
            order = Order.objects.create(ref_code=create_ref_code(), user=request.user, ordered_date=ordered_date)
            order.items.add(order_item)
            messages.info(request, "This item was added to your cart.")
            return redirect("core:order-summary")
        elif item_inventory == 0:
            messages.info(request, "This item is sold out.")
            return redirect("core:product", slug=slug)

@login_required(login_url='users:login')
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        ##If the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            order.items.remove(order_item)
            if order.coupon:
                    for deal in order.coupon.all():
                        if deal.amount > order.item_total():
                            order.coupon.remove(deal)
                            order.save()
            messages.info(request, "This item was removed from your cart.")
            return redirect("core:order-summary")
        ##If the order item is not in the order 
        else:
            messages.info(request, "This item was not in your cart. ")
            return redirect("core:product", slug=slug)
    ##User does not have an active order
    else:
        messages.info(request, "You do not have an active order.")
        return redirect("core:product", slug=slug)

@login_required(login_url='users:login')
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        ##If the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
                if order.coupon:
                    for deal in order.coupon.all():
                        if deal.amount > order.item_total():
                            order.coupon.remove(deal)
                            order.save()
                messages.info(request, "This item quantity was updated.")
                return redirect("core:order-summary")
            else:
                order.items.remove(order_item)
                if order.coupon:
                    for deal in order.coupon.all():
                        if deal.amount > order.item_total():
                            order.coupon.remove(deal)
                            order.save()
                messages.info(request, "This item was removed from your cart.")
                return redirect("core:order-summary")
        ##If the order item is not in the order
        else:
            messages.info(request, "This item was not in your cart.")
            return redirect("core:product", slug=slug)
    ##If the user does not have an active order
    else:
        messages.info(request, "You do not have an active order.")
        return redirect("core:product", slug=slug)

class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(user=self.request.user, ordered=False)
                coupon = Coupon.objects.get(code=code)
                if coupon:
                    if coupon.amount < order.item_total():
                        order.coupon.add(coupon)
                        order.save()
                        messages.success(self.request, "Coupon applied to order.")
                        return redirect("core:order-summary")
                    else:
                        messages.warning(self.request, "Add more to your order to utilize this coupon code")
                        return redirect("core:order-summary")
            except ObjectDoesNotExist:
                messages.warning(self.request, "Invalid Coupon!, please try again!")
                return redirect("core:order-summary")

class AddAddressView(View):
    def post(self, *args, **kwargs):
        form = AddressForm(self.request.POST or None)
        if form.is_valid():
            try:
                form.instance.user = self.request.user
                newAddress = Address(
                    user=self.request.user,
                    street_address=form.instance.street_address,
                    apartment_address=form.instance.apartment_address,
                    city=form.instance.city,
                    state=form.instance.state,
                    zip_code=form.instance.zip_code,
                )
                newAddress.save()
                order = Order.objects.get(user=self.request.user, ordered=False)
                order.shipping_address = newAddress
                order.save()
                messages.success(self.request, "Address included for shipping!")
                return redirect("core:order-summary")
            except ObjectDoesNotExist:
                messages.warning(self.request, "Invalid address, please try again!")
                return redirect("core:order-summary")


class RequestRefundView(View):
    def get(self, *args, **kwargs):
        form = RefundForm()
        context = {
            'form': form,
        }
        return render(self.request, "core/general/request_refund.html", context)

    def post(self, *args, **kwargs):
        form = RefundForm(self.request.POST)
        if form.is_valid():
            ref_code = form.cleaned_data.get('ref_code')
            message = form.cleaned_data.get('message')
            email = form.cleaned_data.get('email')
            ##Edit the order 
            try: 
                order = Order.objects.get(ref_code=ref_code)
                order.refund_requested = True
                order.save()
                ##Store the refund
                refund = Refund()
                refund.order = order
                refund.reason = message
                refund.email = email
                refund.save()
                messages.info(self.request, "Your request was recieved.")
                return redirect("core:request-refund")
            except ObjectDoesNotExist:
                messages.info(self.request, "This order does not exist.")
                return redirect("core:request-refund")

def terms_use(request):
    return render(request, 'core/general/terms_use.html')

def contact(request):
    return render(request, 'core/general/contact.html')

class ItemListView(ListView):
    model = Item
    template_name = "core/shopping/shop_category.html"
    context_object_name = 'items'
    ordering = ['-date_posted']
    paginate_by = 12

    def get_queryset(self):
        category_choice = self.request.GET.get('category_choice')
        if (category_choice is None) or (category_choice == ""):
            new_context = Item.objects.all()
            return new_context
        else:
            new_context = Item.objects.filter(
                category=category_choice,
            )
            return new_context

    def get_context_data(self, **kwargs):
        context = super(ItemListView, self).get_context_data(**kwargs)
        context['category_form'] = CategoryForm()
        if self.request.method == "GET":
            category_choice = self.request.GET.get('category_choice')
            context['category_form'] = CategoryForm(data={'category_choice':category_choice})
        return context

@csrf_exempt
def create_checkout_session(request):
    order = Order.objects.get(user=request.user, ordered=False)
    if order.shipping_address is None:
        messages.warning(request, f'Please include your shipping address!')
        return redirect('core:order-summary')    
    if order.ref_code == "":
        order.ref_code = create_ref_code()
        order.save()
    amount = int(order.get_absolute_total() * 100)
    order_items = []
    for order_item in order.items.all():
        if order_item.item.discount_price:
            order_items.append({
                                'name': str(order_item.item.title),
                                'quantity': int(order_item.quantity),
                                'currency': 'usd',
                                'amount': int(order_item.item.discount_price)*100,
                                'images': [
                                    str(settings.ALLOWED_HOSTS[0] + order_item.item.image.url),
                                    str(settings.ALLOWED_HOSTS[0] + order_item.item.image_sub_one.url),
                                    str(settings.ALLOWED_HOSTS[0] + order_item.item.image_sub_two.url),
                                    str(settings.ALLOWED_HOSTS[0] + order_item.item.image_sub_three.url),
                                ]
                            })
        else:
            order_items.append({
                                'name': str(order_item.item.title),
                                'quantity': int(order_item.quantity),
                                'currency': 'usd',
                                'amount': int(order_item.item.price)*100,
                                'images': [
                                    str(settings.ALLOWED_HOSTS[0] + order_item.item.image.url),
                                    str(settings.ALLOWED_HOSTS[0] + order_item.item.image_sub_one.url),
                                    str(settings.ALLOWED_HOSTS[0] + order_item.item.image_sub_two.url),
                                    str(settings.ALLOWED_HOSTS[0] + order_item.item.image_sub_three.url),
                                ]
                            })
    # shipping
    order_items.append({
                                'name': "Shipping",
                                'quantity': int(1),
                                'currency': 'usd',
                                'amount': int(order.shipping()*100),
                            })
    # tax
    order_items.append({
                                'name': "Processing Fee",
                                'quantity': int(1),
                                'currency': 'usd',
                                'amount': int(order.tax_total()*100),
                            })
    if order.coupon:
        deal_total = 0
        for deal in order.coupon.all():
            deal_total += deal.amount
        if deal_total !=0:   
            customer_coupon = stripe.Coupon.create(
                amount_off=int(deal_total)*100,
                currency= "usd",
            )
            if request.method == 'GET':
                domain_url = settings.ALLOWED_HOSTS[0]
                stripe.api_key = settings.STRIPE_SECRET_KEY
                try:
                    if order.coupon:
                            checkout_session = stripe.checkout.Session.create(
                                    success_url=domain_url + 'success/' +  str(order.ref_code) + '/?session_id={CHECKOUT_SESSION_ID}',
                                    cancel_url=domain_url + 'cancelled/',
                                    client_reference_id=str(order.ref_code),
                                    payment_method_types=['card'],
                                    mode='payment',
                                    customer_email=request.user.email,
                                    line_items=order_items,
                                    metadata={'order_ref_code': order.ref_code},
                                    discounts= [{
                                        'coupon': str(customer_coupon.id)
                                    }]
                                )
                    #return JsonResponse({'sessionId': checkout_session['id']})
                except Exception as e:
                    return JsonResponse({'error': str(e)})
                return redirect(checkout_session.url, code=303)
        else:
            if request.method == 'GET':
                domain_url = settings.ALLOWED_HOSTS[0]
                stripe.api_key = settings.STRIPE_SECRET_KEY
                try:
                    if order.coupon:
                            checkout_session = stripe.checkout.Session.create(
                                    success_url=domain_url + 'success/' +  str(order.ref_code) + '/?session_id={CHECKOUT_SESSION_ID}',
                                    cancel_url=domain_url + 'cancelled/',
                                    client_reference_id=str(order.ref_code),
                                    payment_method_types=['card'],
                                    mode='payment',
                                    customer_email=request.user.email,
                                    line_items=order_items,
                                    metadata={'order_ref_code': order.ref_code},
                                )
                    #return JsonResponse({'sessionId': checkout_session['id']})
                except Exception as e:
                    return JsonResponse({'error': str(e)})
                return redirect(checkout_session.url, code=303)


def success(request, ref_code):
    order = Order.objects.get(ref_code=ref_code)
    if order:
        order.ordered = True
        newPayment = Payment(
            user=request.user,
            amount=order.get_absolute_total()
        )
        newPayment.save()
        order.payment = newPayment
        order.save()

        for order_item in order.items.all():
            item = order_item.item
            item.inventory = item.inventory - order_item.quantity
            order_item.ordered = True
            order_item.save()
            item.save()
        
        # send email 
        subject, from_email, to = 'Thank you for your purchase!', str(settings.EMAIL_HOST_USER), str(order.user.email)
        text_content = 'Order Reference Code - {order.ref_code}\nShipping Address - {order.shipping_address.street_address}, {order.shipping_address.apartment_address}, {order.shipping_address.city}, {order.shipping_address.state}, {order.shipping_address.zip_code}\nOrder Status - {order.status}'
        html_content = '<p>You ordered the following items, please expect shipping to be within 2-3 days.</p>'
        for item in order.items.all():
            item_str = "<p>" + str(item.quantity) + " of " + str(item.item.title) +"</p>"
            html_content += item_str
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        messages.success(request, f'Payment succeeded, please refer to your order below. Expect shipping within 2-3 business days.')
        return redirect('users:profile')
    else:
        messages.warning(request, f'An issue occurred. Not able to find order.')
        return redirect('core:prfile')

def cancelled(request):
    messages.warning(request, f'Payment, cancelled!')
    return redirect('core:order-summary')

class OrderDetailView(DetailView):
    model = Order
    template_name = "core/shopping/order_detail.html"