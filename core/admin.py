from django.contrib import admin
from .models import Item, OrderItem, Order, Payment, Coupon, Refund, CategoryChoice, Address

def make_refund_accepted(modeladmin, request,queryset):
    queryset.update(refund_requested=False, refund_granted=True)

make_refund_accepted.short_description = 'Update orders to refund granted'

class OrderAdmin(admin.ModelAdmin):
    list_display = ['user','ordered','received','being_delievered','refund_requested','refund_granted','payment']
    list_display_links = ['user','payment']
    list_filter = ['ordered','received','being_delievered','refund_requested','refund_granted']
    search_fields = ['user__username','ref_code']
    actions = [make_refund_accepted]

class AddressAdmin(admin.ModelAdmin):
    list_display = ['user','street_address','apartment_address','city','state','zip_code']
    search_fields = ['user','street_address','apartment_address','zip_code']

# Register your models here.
admin.site.register(Item)
admin.site.register(OrderItem)
admin.site.register(Order, OrderAdmin)
admin.site.register(Payment)
admin.site.register(Coupon)
admin.site.register(Refund)
admin.site.register(CategoryChoice)
admin.site.register(Address, AddressAdmin)