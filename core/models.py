from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.shortcuts import reverse
from django_countries.fields import CountryField
from users.models import User, Profile

# Create your models here.
CATEGORY_CHOICES = (
    ('1','Sale'),
    ('2','Limited'),
    ('3','Extreme Sale')
)
LABEL_CHOICES = (
    ('P', 'primary'),
    ('S','secondary'),
    ('D','danger')
)
ADDRESS_CHOICES = (
    ('B', 'Billing'),
    ('S','Shipping'),
)

class Item(models.Model):
    title = models.CharField(max_length=100, verbose_name="Item Name")
    price = models.FloatField()
    discount_price = models.FloatField(blank=True, null=True, verbose_name="Discounted Price")
    category = models.CharField(choices=CATEGORY_CHOICES, max_length=2, null=True, blank=True)
    label = models.CharField(choices=LABEL_CHOICES, max_length=1, default="", verbose_name="Labeled Color")
    slug = models.SlugField(default="", verbose_name="Item Tag", help_text="This text will be used in url. Please use following format: Item-Name-Tag")
    description = models.TextField(default="")
    additional_info = models.TextField(default="", verbose_name="Additional Info")
    image = models.ImageField(blank=False, null=False, verbose_name="Main Image", default="default.png")
    image_sub_one = models.ImageField(blank=False, null=False, verbose_name="Sub Image", default="default.png")
    image_sub_two = models.ImageField(blank=False, null=False, verbose_name="Sub Image", default="default.png")
    image_sub_three = models.ImageField(blank=False, null=False, verbose_name="Sub Image", default="default.png")
    inventory = models.FloatField(default=1)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("core:product", kwargs={'slug': self.slug})

    def get_add_to_cart_url(self):
        return reverse("core:add-to-cart", kwargs={'slug': self.slug})

    def get_remove_from_cart_url(self):
        return reverse("core:remove-from-cart", kwargs={'slug': self.slug})

class OrderItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    ordered = models.BooleanField(default=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)  
    quantity = models.IntegerField(default=1)  

    def __str__(self):
        return f"{self.quantity} of {self.item.title}"

    def get_total_item_price(self):
        return self.quantity * self.item.price
    
    def get_total_discount_item_price(self):
        return self.quantity * self.item.discount_price

    def get_amount_saved(self):
        return self.get_total_item_price() - self.get_total_discount_item_price()
    
    def get_final_price(self):
        if self.item.discount_price:
            return self.get_total_discount_item_price()
        return self.get_total_item_price()

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ref_code = models.CharField(max_length=20, default='')
    items = models.ManyToManyField(OrderItem)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField()
    ordered = models.BooleanField(default=False)
    billing_address = models.ForeignKey('Address', related_name='billing_address', on_delete=models.SET_NULL, blank=True, null=True)
    shipping_address = models.ForeignKey('Address', related_name='shipping_address', on_delete=models.SET_NULL, blank=True, null=True)
    payment = models.ForeignKey('Payment', on_delete=models.SET_NULL, blank=True, null=True)
    coupon = models.ForeignKey('Coupon', on_delete=models.SET_NULL, blank=True, null=True)
    being_delievered = models.BooleanField(default=False)
    received = models.BooleanField(default=False)
    refund_requested = models.BooleanField(default=False)
    refund_granted = models.BooleanField(default=False)

    def __str__(self):
        return super().__str__()
    
    def get_absolute_url(self):
        return reverse("core:order-detail", kwargs={'pk': self.id})
    
    def get_total(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_final_price()
        if self.coupon:
            total -= self.coupon.amount
        return total
    
    def tax_total(self):
        tax = 0 
        tax += (self.get_total() * 0.065)
        return tax

    def get_absolute_total(self):
        absolute_total = 0
        absolute_total += (self.get_total() + self.tax_total())
        return absolute_total


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    street_address = models.CharField(max_length=500)
    apartment_address = models.CharField(max_length=500)
    country = CountryField(multiple=False)
    zip_code = models.CharField(max_length=500)
    address_type = models.CharField(max_length=1, choices=ADDRESS_CHOICES)
    default = models.BooleanField(default=False)

    def __str__(self):
        return self.user.email
    
    class Meta:
        verbose_name_plural = 'Addresses'


class Payment(models.Model):
    stripe_charge_id = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    amount = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.email


class Coupon(models.Model):
    code = models.CharField(max_length=15)
    amount = models.FloatField(default=0)

    def __str__(self):
        return self.code

class Refund(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    reason = models.TextField()
    accepted = models.BooleanField(default=False)
    email = models.EmailField()

    def __str__(self):
        return f"{self.pk}"
