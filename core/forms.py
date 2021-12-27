from django import forms
from core.models import CategoryChoice
from users.models import User
from core.models import Item, Address

class CouponForm(forms.Form):
    code = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Promo code',
        'aria-label': 'Reicipent\'s username',
        'aria-describedby': 'basic-addon2'
    }))

class RefundForm(forms.Form):
    ref_code = forms.CharField()
    message = forms.CharField(widget=forms.Textarea(attrs={
        'rows': 4,
    }))
    email = forms.EmailField()

class PaymentForm(forms.Form):
    stripeToken = forms.CharField(required=False)
    save = forms.BooleanField(required=False)
    use_default = forms.BooleanField(required=False)


class UserUpdateForm(forms.ModelForm):
    email: forms.EmailField()

    class Meta:
        model = User
        fields = ['email']

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['street_address', 'apartment_address','city','state','zip_code']

    def __init__(self, *args, **kwargs):
        super(AddressForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'

class CategoryForm(forms.Form):
    category_choice = forms.ModelChoiceField(queryset = CategoryChoice.objects.all(), required=False)

    def __init__(self, *args, **kwargs):
        super(CategoryForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'