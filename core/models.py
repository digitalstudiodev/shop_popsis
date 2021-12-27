from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.shortcuts import reverse
from users.models import User, Profile

LABEL_CHOICES = (
    ('P', 'primary'),
    ('S','secondary'),
    ('D','danger')
)

STATES = (
    ('AL', ('Alabama')),
    ('AZ', ('Arizona')),
    ('AR', ('Arkansas')),
    ('CA', ('California')),
    ('CO', ('Colorado')),
    ('CT', ('Connecticut')),
    ('DE', ('Delaware')),
    ('DC', ('District of Columbia')),
    ('FL', ('Florida')),
    ('GA', ('Georgia')),
    ('ID', ('Idaho')),
    ('IL', ('Illinois')),
    ('IN', ('Indiana')),
    ('IA', ('Iowa')),
    ('KS', ('Kansas')),
    ('KY', ('Kentucky')),
    ('LA', ('Louisiana')),
    ('ME', ('Maine')),
    ('MD', ('Maryland')),
    ('MA', ('Massachusetts')),
    ('MI', ('Michigan')),
    ('MN', ('Minnesota')),
    ('MS', ('Mississippi')),
    ('MO', ('Missouri')),
    ('MT', ('Montana')),
    ('NE', ('Nebraska')),
    ('NV', ('Nevada')),
    ('NH', ('New Hampshire')),
    ('NJ', ('New Jersey')),
    ('NM', ('New Mexico')),
    ('NY', ('New York')),
    ('NC', ('North Carolina')),
    ('ND', ('North Dakota')),
    ('OH', ('Ohio')),
    ('OK', ('Oklahoma')),
    ('OR', ('Oregon')),
    ('PA', ('Pennsylvania')),
    ('RI', ('Rhode Island')),
    ('SC', ('South Carolina')),
    ('SD', ('South Dakota')),
    ('TN', ('Tennessee')),
    ('TX', ('Texas')),
    ('UT', ('Utah')),
    ('VT', ('Vermont')),
    ('VA', ('Virginia')),
    ('WA', ('Washington')),
    ('WV', ('West Virginia')),
    ('WI', ('Wisconsin')),
    ('WY', ('Wyoming')),
)



class CategoryChoice(models.Model):
    category_choice = models.CharField(max_length=100, verbose_name="Category Choice")
    image = models.ImageField(blank=False, null=False, verbose_name="Category Image", default="default.png", upload_to='category_pics')

    def __str__(self):
        return self.category_choice

    def get_absolute_url(self):
        return reverse("dashboard:category-detail", kwargs={'pk': self.id})

class Item(models.Model):
    title = models.CharField(max_length=100, verbose_name="Item Name")
    price = models.FloatField()
    discount_price = models.FloatField(blank=True, null=True, verbose_name="Discounted Price")
    category = models.ForeignKey(CategoryChoice, on_delete=models.CASCADE, blank=True, null=True)
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
        return reverse("dashboard:item-detail", kwargs={'pk': self.pk})

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


class Payment(models.Model):
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
        return reverse("dashboard:coupon-detail", kwargs={'pk': self.id})

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ref_code = models.CharField(max_length=20, default='')
    items = models.ManyToManyField(OrderItem)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField()
    ordered = models.BooleanField(default=False)
    payment = models.ForeignKey('Payment', on_delete=models.SET_NULL, blank=True, null=True)
    shipping_address = models.ForeignKey('Address', related_name='shipping_address', on_delete=models.SET_NULL, blank=True, null=True)
    coupon = models.ManyToManyField(Coupon)
    being_delievered = models.BooleanField(default=False)
    received = models.BooleanField(default=False)
    refund_requested = models.BooleanField(default=False)
    refund_granted = models.BooleanField(default=False)

    def __str__(self):
        return super().__str__()
    
    def get_absolute_url(self):
        return reverse("core:order-detail", kwargs={'pk': self.id})
    
    def item_total(self):
        total = 0
        for order_item in self.items.all():
            total += round(order_item.get_final_price(), 2)
        return round(total,2)
        
    def get_total(self):
        total = 0
        for order_item in self.items.all():
            total += round(order_item.get_final_price(), 2)
        if self.coupon:
            for deal in self.coupon.all():
                total -= round(deal.amount, 2)
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


class Refund(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    reason = models.TextField()
    accepted = models.BooleanField(default=False)
    email = models.EmailField()

    def __str__(self):
        return f"{self.pk}"

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    street_address = models.CharField(max_length=500, blank=False, null=False)
    apartment_address = models.CharField(max_length=500, blank=True, null=True)
    city = models.CharField(max_length=500, blank=False, null=False)
    state = models.CharField(max_length=500, choices=STATES)
    zip_code = models.CharField(max_length=10, blank=False, null=False)

    def __str__(self):
        return self.user.email
    
    class Meta:
        verbose_name_plural = 'Addresses'