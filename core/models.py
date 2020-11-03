from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.shortcuts import reverse
from django_countries.fields import CountryField
from users.models import User, Profile

# Create your models here.
CATEGORY_CHOICES = (
    ('1','Earrings'),
    ('2','Bags'),
    ('3','Lip Gloss')
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
    image = models.ImageField(blank=False, null=False, verbose_name="Main Image", default="default.png", upload_to='item_pics')
    image_sub_one = models.ImageField(blank=False, null=False, verbose_name="Sub Image", default="default.png", upload_to='item_pics')
    image_sub_two = models.ImageField(blank=False, null=False, verbose_name="Sub Image", default="default.png", upload_to='item_pics')
    image_sub_three = models.ImageField(blank=False, null=False, verbose_name="Sub Image", default="default.png", upload_to='item_pics')
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
        return round(self.quantity * self.item.price,2)
    
    def get_total_discount_item_price(self):
        return round(self.quantity * self.item.discount_price)

    def get_amount_saved(self):
        return "{:.2f}".format(self.get_total_item_price() - self.get_total_discount_item_price())
    
    def get_final_price(self):
        if self.item.discount_price:
            return round(self.get_total_discount_item_price(),2)
        return round(self.get_total_item_price(),2)

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
            total += round(order_item.get_final_price(), 2)
        if self.coupon:
            total -= round(self.coupon.amount, 2)
        return round(total,2)
    
    def tax_total(self):
        tax = 0 
        tax += round((self.get_total() * 0.07), 2)
        return round(tax,2)

    def shipping(self):
        return 5

    def get_absolute_total(self):
        absolute_total = 0
        absolute_total += round((self.get_total() + self.tax_total() + self.shipping()), 2)
        if absolute_total >= 0: 
            return round(absolute_total,2)
        else:
            return 0
    
    def status(self):
        if self.being_delievered:
            return "Being Delivered"
        elif self.received:
            return "Received"
        elif not self.being_delievered or not self.received:
            return "Pending"


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
    
    def get_absolute_url(self):
        return reverse("dashboard:dashboard")

class Refund(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    reason = models.TextField()
    accepted = models.BooleanField(default=False)
    email = models.EmailField()

    def __str__(self):
        return f"{self.pk}"
