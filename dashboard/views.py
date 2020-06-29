from django.shortcuts import render
from core.models import Order, Item, Coupon

# Create your views here.
def dashboard(request):
    try: 
        orders = Order.objects.all()
        items = Item.objects.all()
        coupons = Coupon.objects.all()
        total_sales = 0
        order_dates = [] 
        order_payments = []
        for o in orders.order_by('ordered_date')[:5]:
            order_dates.append(str(o.ordered_date.strftime("%b %d")))
            order_payments.append(int(o.payment.amount))
        for o in orders:
            if o.payment.amount:
                total_sales += o.payment.amount
    except: 
        pass
    context = {
        'items': items,
        'orders': orders,
        'sales': round(total_sales, 2),
        'order_dates': order_dates,
        'order_payments': order_payments,
        'coupons': coupons,
    }
    return render(request, "dashboard/dashboard.html", context)