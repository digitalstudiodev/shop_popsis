from django.conf import settings as settings
from django.urls import reverse
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, get_object_or_404, redirect, render
from django.views.generic import ListView, DetailView, View,CreateView, UpdateView, DeleteView
from django.utils import timezone
from .forms import CheckoutForm, CouponForm, RefundForm, PaymentForm, UserUpdateForm
from .models import Item, OrderItem, Order, Address, Payment, Coupon, Refund
from users.models import User, Profile
import random
import string
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

class CheckoutView(View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            form = CheckoutForm()
            context = {
                'form': form,
                'couponform': CouponForm(),
                'order': order,
                'DISPLAY_COUPON_FORM': True
            }

            shipping_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type='S',
                default=True
            )
            if shipping_address_qs.exists():
                context.update(
                    {'default_shipping_address': shipping_address_qs[0]})

            billing_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type='B',
                default=True
            )
            if billing_address_qs.exists():
                context.update(
                    {'default_billing_address': billing_address_qs[0]})

            return render(self.request, "checkout.html", context)
        except ObjectDoesNotExist:
            messages.info(self.request, "You do not have an active order")
            return redirect("core:checkout")

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():

                use_default_shipping = form.cleaned_data.get(
                    'use_default_shipping')
                if use_default_shipping:
                    print("Using the defualt shipping address")
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='S',
                        default=True
                    )
                    if address_qs.exists():
                        shipping_address = address_qs[0]
                        order.shipping_address = shipping_address
                        order.save()
                    else:
                        messages.info(
                            self.request, "No default shipping address available")
                        return redirect('core:checkout')
                else:
                    print("User is entering a new shipping address")
                    shipping_address1 = form.cleaned_data.get(
                        'shipping_address')
                    shipping_address2 = form.cleaned_data.get(
                        'shipping_address2')
                    shipping_country = form.cleaned_data.get(
                        'shipping_country')
                    shipping_zip = form.cleaned_data.get('shipping_zip')

                    if is_valid_form([shipping_address1, shipping_country, shipping_zip]):
                        shipping_address = Address(
                            user=self.request.user,
                            street_address=shipping_address1,
                            apartment_address=shipping_address2,
                            country=shipping_country,
                            zip_code=shipping_zip,
                            address_type='S'
                        )
                        shipping_address.save()

                        order.shipping_address = shipping_address
                        order.save()

                        set_default_shipping = form.cleaned_data.get(
                            'set_default_shipping')
                        if set_default_shipping:
                            shipping_address.default = True
                            shipping_address.save()

                    else:
                        messages.info(
                            self.request, "Please fill in the required shipping address fields")

                use_default_billing = form.cleaned_data.get(
                    'use_default_billing')
                same_billing_address = form.cleaned_data.get(
                    'same_billing_address')

                if same_billing_address:
                    billing_address = shipping_address
                    billing_address.pk = None
                    billing_address.save()
                    billing_address.address_type = 'B'
                    billing_address.save()
                    order.billing_address = billing_address
                    order.save()

                elif use_default_billing:
                    print("Using the defualt billing address")
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='B',
                        default=True
                    )
                    if address_qs.exists():
                        billing_address = address_qs[0]
                        order.billing_address = billing_address
                        order.save()
                    else:
                        messages.info(
                            self.request, "No default billing address available")
                        return redirect('core:checkout')
                else:
                    print("User is entering a new billing address")
                    billing_address1 = form.cleaned_data.get(
                        'billing_address')
                    billing_address2 = form.cleaned_data.get(
                        'billing_address2')
                    billing_country = form.cleaned_data.get(
                        'billing_country')
                    billing_zip = form.cleaned_data.get('billing_zip')

                    if is_valid_form([billing_address1, billing_country, billing_zip]):
                        billing_address = Address(
                            user=self.request.user,
                            street_address=billing_address1,
                            apartment_address=billing_address2,
                            country=billing_country,
                            zip_code=billing_zip,
                            address_type='B'
                        )
                        billing_address.save()

                        order.billing_address = billing_address
                        order.save()

                        set_default_billing = form.cleaned_data.get(
                            'set_default_billing')
                        if set_default_billing:
                            billing_address.default = True
                            billing_address.save()

                    else:
                        messages.info(
                            self.request, "Please fill in the required billing address fields")
                '''
                payment_option = form.cleaned_data.get('payment_option')

                if payment_option == 'S':
                    return redirect('core:payment', payment_option='stripe')
                elif payment_option == 'P':
                    return redirect('core:payment', payment_option='paypal')
                else:
                    messages.warning(
                        self.request, "Invalid payment option selected")
                    return redirect('core:checkout')
                '''
                return redirect('core:payment')
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("core:order-summary")


class PaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        if order.billing_address:
            context = {
                'order': order,
                'DISPLAY_COUPON_FORM': False
            }
            userprofile = self.request.user.profile
            if userprofile.one_click_purchasing:
                # fetch the users card list
                cards = stripe.Customer.list_sources(
                    userprofile.stripe_customer_id,
                    limit=3,
                    object='card'
                )
                card_list = cards['data']
                if len(card_list) > 0:
                    # update the context with the default card
                    context.update({
                        'card': card_list[0]
                    })
            return render(self.request, "payment.html", context)
        else:
            messages.warning(
                self.request, "You have not added a billing address")
            return redirect("core:checkout")

    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        form = PaymentForm(self.request.POST)
        userprofile = Profile.objects.get(user=self.request.user)
        if form.is_valid():
            token = form.cleaned_data.get('stripeToken')
            save = form.cleaned_data.get('save')
            use_default = form.cleaned_data.get('use_default')

            if save:
                if userprofile.stripe_customer_id != '' and userprofile.stripe_customer_id is not None:
                    customer = stripe.Customer.retrieve(userprofile.stripe_customer_id)
                    customer.sources.create(source=token)

                else:
                    customer = stripe.Customer.create(email=self.request.user.email,)
                    customer.sources.create(source=token)
                    userprofile.stripe_customer_id = customer['id']
                    userprofile.one_click_purchasing = True
                    userprofile.save()

            amount = int(order.get_absolute_total() * 100)

            try:
                if use_default or save:
                    # charge the customer because we cannot charge the token more than once
                    charge = stripe.Charge.create(
                        amount=amount,  # cents
                        currency="usd",
                        customer=userprofile.stripe_customer_id,
                        receipt_email=self.request.user.email,
                    )
                else:
                    # charge once off on the token
                    charge = stripe.Charge.create(
                        amount=amount,  # cents
                        currency="usd",
                        source=token,
                        receipt_email=self.request.user.email,
                    )

                # create the payment
                payment = Payment()
                payment.stripe_charge_id = charge['id']
                payment.user = self.request.user
                payment.amount = order.get_absolute_total()
                payment.save()

                # assign the payment to the order
                order_items = order.items.all()
                order_items.update(ordered=True)
                for item in order_items:
                    item.save()

                order.ordered = True
                order.payment = payment
                order.ref_code = create_ref_code()
                order.save()

                messages.success(self.request, "Your order was successful!")
                return redirect("users:profile")

            except stripe.error.CardError as e:
                body = e.json_body
                err = body.get('error', {})
                messages.warning(self.request, f"{err.get('message')}")
                return redirect("/")

            except stripe.error.RateLimitError as e:
                # Too many requests made to the API too quickly
                messages.warning(self.request, "Rate limit error")
                return redirect("/")

            except stripe.error.InvalidRequestError as e:
                # Invalid parameters were supplied to Stripe's API
                print(e)
                messages.warning(self.request, "Invalid parameters")
                return redirect("/")

            except stripe.error.AuthenticationError as e:
                # Authentication with Stripe's API failed
                # (maybe you changed API keys recently)
                messages.warning(self.request, "Not authenticated")
                return redirect("/")

            except stripe.error.APIConnectionError as e:
                # Network communication with Stripe failed
                messages.warning(self.request, "Network error")
                return redirect("/")

            except stripe.error.StripeError as e:
                # Display a very generic error to the user, and maybe send
                # yourself an email
                messages.warning(
                    self.request, "Something went wrong. You were not charged. Please try again.")
                return redirect("/")

            except Exception as e:
                # send an email to ourselves
                messages.warning(
                    self.request, "A serious error occurred. We have been notifed.")
                return redirect("/")

        messages.warning(self.request, "Invalid data received")
        return redirect("/payment/stripe/")

def home(request):
    context = {
        'items': Item.objects.all()[:16]
    }
    return render(request, "core/home.html", context)

class HomeView(ListView):
    model = Item
    paginate_by = 4
    template_name = "core/home.html"

class ShopView(ListView):
    model = Item
    paginate_by = 10
    template_name = "core/shop.html"

class SaleView(ListView):
    model = Item
    paginate_by = 10
    template_name = "core/sale.html"

class LimitedView(ListView):
    model = Item
    paginate_by = 10
    template_name = "core/limited.html"

class ExtremeSaleView(ListView):
    model = Item
    paginate_by = 10
    template_name = "core/extreme_sale.html"

class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object': order
            }
            return render(self.request, 'core/order_summary.html', context)
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("core:home")

class ItemDetailView(DetailView):
    model = Item
    template_name = "core/product.html"

class OrderDetailView(DetailView):
    model = Order
    template_name = "core/order_detail.html"

class OrderUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Order
    fields = [ 
        'refund_granted', 'being_delievered', 'received'
    ]

    def form_valid(self, form):
        messages.success(self.request, f'You have successfully updated the item')
        return super().form_valid(form)

    def test_func(self):
        item = self.get_object()
        if self.request.user.is_superuser:
            return True
        return False

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
    print(item_inventory)

    ##If item is in user order
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            if item_inventory > 1:
                item_inventory -= 1
                order_item.item.inventory = item_inventory
                order_item.item.save()
                order_item.quantity += 1
                order_item.save()
                messages.info(request, "This item quantity was updated.")
                return redirect("core:order-summary")
            elif item_inventory == 1:
                item_inventory = 0
                order_item.item.inventory = item_inventory
                order_item.item.save()
                order_item.quantity += 1
                order_item.save()
                messages.info(request, "This item quantity was updated. You're buying the last one.")
                return redirect("core:order-summary")
            elif item_inventory == 0:
                messages.info(request, "This item is sold out.")
                return redirect("core:order-summary")
        else:
            if item_inventory > 1:
                item_inventory -= 1
                order_item.item.inventory = item_inventory
                order_item.item.save()
                order.items.add(order_item)
                messages.info(request, "This item was added to your cart.")
                return redirect("core:order-summary")
            elif item_inventory == 1:
                item_inventory = 0
                order_item.item.inventory = item_inventory
                order_item.item.save()
                order.items.add(order_item)
                messages.info(request, "This item was added to your cart. You're buying the last one.")
                return redirect("core:order-summary")
            elif item_inventory == 0:
                messages.info(request, "This item is sold out.")
                return redirect("core:product", slug=slug)
    ##If item is not in user order
    else:
        if item_inventory > 1:
            item_inventory -= 1
            order_item.item.inventory = item_inventory
            order_item.item.save()
            ordered_date = timezone.now()
            order = Order.objects.create(user=request.user, ordered_date=ordered_date)
            order.items.add(order_item)
            messages.info(request, "This item was added to your cart.")
            return redirect("core:order-summary")
        elif item_inventory == 1:
            item_inventory = 0
            order_item.item.inventory = item_inventory
            order_item.item.save()
            ordered_date = timezone.now()
            order = Order.objects.create(user=request.user, ordered_date=ordered_date)
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
            order_item.item.inventory += order_item.quantity
            order_item.item.save()
            order.items.remove(order_item)
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
                order_item.item.inventory += 1
                order_item.item.save()
                order_item.save()
                messages.info(request, "This item quantity was updated.")
                return redirect("core:order-summary")
            else:
                order_item.item.inventory += order_item.quantity
                order_item.item.save()
                order.items.remove(order_item)
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


def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon
    except ObjectDoesNotExist:
        messages.info(request, "Invalid Coupon.")
        return redirect("core:checkout")

class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(user=self.request.user, ordered=False)
                order.coupon = get_coupon(self.request, code)
                order.save()
                messages.success(self.request, "Coupon applied to order.")
                return redirect("core:checkout")
            except ObjectDoesNotExist:
                messages.info(self.request, "You do not have an active order.")
                return redirect("core:checkout")

class RequestRefundView(View):
    def get(self, *args, **kwargs):
        form = RefundForm()
        context = {
            'form': form,
        }
        return render(self.request, "request_refund.html", context)

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

def shipping_return(request):
    return render(request, 'core/shipping_return.html')

def privacy_policy(request):
    return render(request, 'core/privacy_policy.html')

def terms_use(request):
    return render(request, 'core/terms_use.html')

def about_us(request):
    return render(request, 'core/about_us.html')

def contact(request):
    return render(request, 'core/contact.html')

@login_required(login_url='users:login')
def dashboard(request):
    context = {
        'items': Item.objects.all(),
        'orders': Order.objects.all(),
        'coupon': Coupon.objects.all(),
    }
    return render(request, 'core/dashboard.html', context)

class ItemCreateView(LoginRequiredMixin, CreateView):
    model = Item
    fields = [
        'title', 'price', 'discount_price', 'category', 'label',
        'slug', 'description', 'additional_info', 'image', 'image_sub_one',
        'image_sub_two', 'image_sub_three', 'inventory'
    ]

    def form_valid(self, form):
        messages.success(self.request, f'You have successfully added a new item')
        return super().form_valid(form)

class ItemUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Item
    fields = [
        'title', 'price', 'discount_price', 'category', 'label',
        'slug', 'description', 'additional_info', 'image', 'image_sub_one',
        'image_sub_two', 'image_sub_three', 'inventory'
    ]

    def form_valid(self, form):
        messages.success(self.request, f'You have successfully updated the item')
        return super().form_valid(form)

    def test_func(self):
        item = self.get_object()
        if self.request.user.is_superuser:
            return True
        return False

class ItemDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Item
    success_url = '/'

    def test_func(self):
        item = self.get_object()
        if self.request.user.is_superuser:
            return True
        return False


def new_base(request):
    return render(request, "core/new_base.html")

class CouponCreateView(LoginRequiredMixin, CreateView):
    model = Coupon
    fields = [
        'code', 'amount'
    ]

    def form_valid(self, form):
        messages.success(self.request, f'You have successfully added a new coupon')
        return super().form_valid(form)

class CouponDetailView(DetailView):
    model = Coupon

class CouponUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Coupon
    fields = [
        'code', 'amount'
    ]

    def form_valid(self, form):
        messages.success(self.request, f'You have successfully updated the coupon')
        return super().form_valid(form)

    def test_func(self):
        item = self.get_object()
        if self.request.user.is_superuser:
            return True
        return False

class CouponDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Coupon
    success_url = '/dashboard/'

    def test_func(self):
        coupon = self.get_object()
        if self.request.user.is_superuser:
            return True
        return False
