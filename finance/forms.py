from django import forms
from django.core.exceptions import ValidationError

from accounts.models import User
from finance.models import Prices, SellersPrices


class DenyForm(forms.Form):
    reason = forms.CharField(widget=forms.Textarea, max_length=100)
    delete_all_configs = forms.BooleanField(required=False)
    delete_last_config = forms.BooleanField(required=False)
    disable_all_configs = forms.BooleanField(required=False)
    disable_last_config = forms.BooleanField(required=False)
    ban_user = forms.BooleanField(required=False)


class EditPayPriceForm(forms.Form):
    price = forms.IntegerField(required=True,widget=forms.TextInput(attrs={'placeholder': 'قیمت جدید / هزارتومان'}))
    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price:
            if not 5 < price < 999:
                raise ValidationError('قیمت باید بین 5 تا 999 هزار تومان باشد.')
        else:
            raise ValidationError("قیمت را وارد کنید.")
        return price * 1000



class AddPriceForm(forms.Form):
    type_conf = forms.ChoiceField(choices=[("limited", "حجمی"), ("inf_usage", "حجم نامحدود"), ("inf_time", "زمان نامحدود")])
    usage = forms.IntegerField(initial=0)
    month = forms.ChoiceField(choices=[(1,"1 ماه"),(2,"2 ماه"),(3,"3 ماه"),(6,"6 ماه")])
    ip_limit = forms.ChoiceField(choices=[(1,"1 کاربره"),(2,"2 کاربره")])
    price = forms.IntegerField(required=True)

    def clean(self):
        price = self.cleaned_data.get('price')
        usage = self.cleaned_data.get('usage')
        type_conf = self.cleaned_data.get('type_conf')
        ip_limit = self.cleaned_data.get('ip_limit')
        month = self.cleaned_data.get('month')
        if price:
            if not 10 < price < 999 :
                raise ValidationError('قیمت باید بین 10 تا 999 هزار تومان باشد.')
        else:
            raise ValidationError("قیمت را وارد کنید.")
        if type_conf == "limited" or type_conf == 'inf_time':
            if not 2 < usage < 900:
                raise ValidationError("حجم کانفیگ باید بین 2 تا 900 گیگ باشد.")

        if type_conf == "limited":
            ip_limit = 0
        elif type_conf == "inf_usage":
            usage = 0
        elif type_conf == "inf_time":
            month = 0
        if Prices.objects.filter(
                user_limit=int(ip_limit),
                usage_limit=int(usage),
                expire_limit=int(month)).exists():
            raise ValidationError("این تعرفه قبلا ثبت شده است.")

class SellersAddPriceForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.username = kwargs.pop('username', None)
        super().__init__(*args, **kwargs)

    type_conf = forms.ChoiceField(choices=[("limited", "حجمی"), ("inf_usage", "حجم نامحدود"), ("inf_time", "زمان نامحدود")])
    usage = forms.IntegerField(initial=0)
    month = forms.ChoiceField(choices=[(1,"1 ماه"),(2,"2 ماه"),(3,"3 ماه"),(6,"6 ماه")])
    ip_limit = forms.ChoiceField(choices=[(1,"1 کاربره"),(2,"2 کاربره")])
    price = forms.IntegerField(required=True)

    def clean(self):
        price = self.cleaned_data.get('price')
        usage = self.cleaned_data.get('usage')
        type_conf = self.cleaned_data.get('type_conf')
        ip_limit = self.cleaned_data.get('ip_limit')
        month = self.cleaned_data.get('month')
        if price:
            if not 10 < price < 999 :
                raise ValidationError('قیمت باید بین 10 تا 999 هزار تومان باشد.')
        else:
            raise ValidationError("قیمت را وارد کنید.")
        if type_conf == "limited" or type_conf == 'inf_time':
            if not 2 < usage < 900:
                raise ValidationError("حجم کانفیگ باید بین 2 تا 900 گیگ باشد.")

        if type_conf == "limited":
            ip_limit = 0
        elif type_conf == "inf_usage":
            usage = 0
        elif type_conf == "inf_time":
            month = 0
        if SellersPrices.objects.filter(
                seller=User.objects.get(username=self.username),
                user_limit=int(ip_limit),
                usage_limit=int(usage),
                expire_limit=int(month)).exists():
            raise ValidationError("این تعرفه قبلا ثبت شده است.")


class AddOffForm(forms.Form):
    type_off = forms.ChoiceField(choices=[(1, "درصدی (%)"), (0, "مقداری (تومان)")], required=False)
    amount = forms.IntegerField(min_value=1, max_value=50, required=False)
    curumer_count = forms.IntegerField(initial=0, min_value=0 , max_value=500, required=False)
    use_count = forms.ChoiceField(choices=[(1, "1 بار"),(0,"چندین بار")])
    end_time = forms.ChoiceField(choices=[(1,"1 روز"), (2,"2 روز"), (3,"3 روز"), (5,"5 روز"), (7,"7 روز"), (10,"10 روز"), (20,"20 روز"), (30,"30 روز"), (60,"60 روز")], required=False)
    for_infinit_usages = forms.BooleanField(initial=True, required=False)
    for_infinit_times = forms.BooleanField(initial=True, required=False)
    for_not_infinity = forms.BooleanField(initial=True, required=False)

    def clean(self):
        amount = self.cleaned_data.get('amount')
        print(amount)
        if not amount:
            raise ValidationError("مقداد تخفیف را وارد کنید.")


class PriceForm(forms.Form):
    price = forms.IntegerField(initial=0, required=False, max_value=10000)
