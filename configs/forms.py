from django import forms
from finance.models import Prices, SellersPrices
from django.core.exceptions import ValidationError
from django.db.models import Q
from accounts.models import User


class SearchConfigForm(forms.Form):
    search_config = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'placeholder': 'Search Config Name or UUID'}))


class CreateConfigForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["type"].choices = self.type_limit()
    def type_limit(self):
        types = [('limited','حجمی')]
        if Prices.objects.filter(usage_limit=0).exists():
            types.append(('usage_unlimit', "حجم نامحدود"))
        if Prices.objects.filter(expire_limit=0).exists():
            types.append(('time_unlimit', "زمان نامحدود"))
        return types


    type = forms.ChoiceField(required=False,)
    usage_limit = forms.CharField(required=False, widget=forms.Select(choices=[]))
    days_limit = forms.CharField(required=False, widget=forms.Select(choices=[]))
    ip_limit = forms.CharField(required=False, widget=forms.Select(choices=[]))
    paid = forms.BooleanField(required=False, initial=True)
    def clean_usage_limit(self):
        return self.cleaned_data.get('usage_limit')
    def clean_days_limit(self):
        return self.cleaned_data.get('days_limit')
    def clean_ip_limit(self):
        return self.cleaned_data.get('ip_limit')



class ManualCreateConfigForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["type"].choices = self.type_limit()
    def type_limit(self):
        types = [('limited','حجمی')]
        if Prices.objects.filter(usage_limit=0).exists():
            types.append(('usage_unlimit', "حجم نامحدود"))
        if Prices.objects.filter(expire_limit=0).exists():
            types.append(('time_unlimit', "زمان نامحدود"))
        return types

    type = forms.ChoiceField(required=False)
    usage_limit = forms.IntegerField(required=False)
    days_limit = forms.IntegerField(required=False)
    ip_limit = forms.ChoiceField(required=False, choices=[(1, '1 کاربره'), (2, '2 کاربره')])
    price = forms.IntegerField(required=False)
    paid = forms.BooleanField(required=False, initial=True)

    def clean_price(self):
        price = self.cleaned_data['price']
        if price is None:
            raise ValidationError('قیمت را وارد کنید.')
        elif not 0 <= price < 1500:
            raise ValidationError('قیمت باید بین 0 تا 1500 هزار تومان باشد.')
        return price

    def clean(self):
        type = self.cleaned_data.get('type')
        usage_limit = self.cleaned_data.get('usage_limit')
        days_limit = self.cleaned_data.get('days_limit')
        if type == "limited":
            if usage_limit is None:
                raise ValidationError('حجم کانفیگ را وارد کنید.')
            elif not 1 < usage_limit < 1000:
                raise ValidationError('حجم کانفیگ باید بین 1 تا 1000 گیگ باشد.')
            if days_limit is None:
                raise ValidationError('مدت زمان کانفیگ را وارد کنید.')
            elif not 0 < days_limit < 365:
                raise ValidationError('مدت زمان کانفیگ باید بین 1 روز تا 365 روز باشد.')
        elif type == 'usage_unlimit':
            if days_limit is None:
                raise ValidationError('مدت زمان کانفیگ را وارد کنید.')
            elif not 0 < days_limit < 365:
                raise ValidationError('مدت زمان کانفیگ باید بین 1 روز تا 365 روز باشد.')
        elif type == 'time_unlimit':
            if usage_limit is None:
                raise ValidationError('حجم کانفیگ را وارد کنید.')
            elif not 1 < usage_limit < 1000:
                raise ValidationError('حجم کانفیگ باید بین 1 تا 1000 گیگ باشد.')


class ChangeConfigSettingForm(forms.Form):

    usage_limit = forms.IntegerField(required=False)
    days_limit = forms.IntegerField(required=False)
    ip_limit = forms.IntegerField(required=False)

    def clean(self):
        usage_limit = self.cleaned_data.get('usage_limit')
        days_limit = self.cleaned_data.get('days_limit')
        ip_limit = self.cleaned_data.get("ip_limit")
        if usage_limit is None:
            raise ValidationError('حجم کانفیگ را وارد کنید.')
        elif not 0 <= usage_limit < 1000:
            raise ValidationError('حجم کانفیگ باید بین 1 تا 1000 گیگ باشد.')
        if days_limit is None:
            raise ValidationError('مدت زمان کانفیگ را وارد کنید.')
        elif not 0 <= days_limit < 181:
            raise ValidationError('مدت زمان کانفیگ باید بین 1 تا 180 روز باشد.')
        if not 0 <= ip_limit <= 4:
            raise ValidationError('محدودیت آی پی باید بین 0 تا 4 باشد.')



###################################### sellers


class SellersCreateConfigForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.username = kwargs.pop('username')
        super().__init__(*args, **kwargs)
        self.fields["type"].choices = self.type_limit()
    def type_limit(self):
        types = []
        if SellersPrices.objects.filter(~Q(usage_limit=0), ~Q(expire_limit=0),seller__username=self.username).exists():
            types = [('limited','حجمی')]
        if SellersPrices.objects.filter(usage_limit=0, seller__username=self.username).exists():
            types.append(('usage_unlimit', "حجم نامحدود"))
        if SellersPrices.objects.filter(expire_limit=0, seller__username=self.username).exists():
            types.append(('time_unlimit', "زمان نامحدود"))
        return types


    type = forms.ChoiceField(required=False,)
    usage_limit = forms.CharField(required=False, widget=forms.Select(choices=[]))
    days_limit = forms.CharField(required=False, widget=forms.Select(choices=[]))
    ip_limit = forms.CharField(required=False, widget=forms.Select(choices=[]))
    paid = forms.BooleanField(required=False, initial=True)
    def clean_usage_limit(self):
        return self.cleaned_data.get('usage_limit')
    def clean_days_limit(self):
        return self.cleaned_data.get('days_limit')
    def clean_ip_limit(self):
        return self.cleaned_data.get('ip_limit')



class ManualSellersCreateConfigForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.username = kwargs.pop('username')
        super().__init__(*args, **kwargs)
    type = forms.ChoiceField(required=False,choices=[('limited','حجمی'),('usage_unlimit', "حجم نامحدود"), ('time_unlimit', "زمان نامحدود")])
    usage_limit = forms.IntegerField(required=False)
    days_limit = forms.IntegerField(required=False)
    ip_limit = forms.ChoiceField(required=False, choices=[(1, '1 کاربره'), (2, '2 کاربره')])
    price = forms.IntegerField(required=False)
    paid = forms.BooleanField(required=False, initial=True)

    def clean_price(self):
        price = self.cleaned_data['price']
        if price is None:
            raise ValidationError('قیمت را وارد کنید.')
        elif not 0 <= price < 1500:
            raise ValidationError('قیمت باید بین 0 تا 1500 هزار تومان باشد.')
        return price

    def clean(self):
        type = self.cleaned_data.get('type')
        usage_limit = self.cleaned_data.get('usage_limit')
        days_limit = self.cleaned_data.get('days_limit')
        if type == "limited":
            if usage_limit is None:
                raise ValidationError('حجم کانفیگ را وارد کنید.')
            elif not 1 < usage_limit < 1000:
                raise ValidationError('حجم کانفیگ باید بین 1 تا 1000 گیگ باشد.')
            if days_limit is None:
                raise ValidationError('مدت زمان کانفیگ را وارد کنید.')
            elif not 0 < days_limit < 365:
                raise ValidationError('مدت زمان کانفیگ باید بین 1 روز تا 365 روز باشد.')
        elif type == 'usage_unlimit':
            if days_limit is None:
                raise ValidationError('مدت زمان کانفیگ را وارد کنید.')
            elif not 0 < days_limit < 365:
                raise ValidationError('مدت زمان کانفیگ باید بین 1 روز تا 365 روز باشد.')
        elif type == 'time_unlimit':
            if usage_limit is None:
                raise ValidationError('حجم کانفیگ را وارد کنید.')
            elif not 1 < usage_limit < 1000:
                raise ValidationError('حجم کانفیگ باید بین 1 تا 1000 گیگ باشد.')



class DisableAllForm(forms.Form):
    @staticmethod
    def sellers_cj():
        l = [(None,"-------")]
        for i in User.objects.filter(level_access__in=[0,1]):
            l.append((i.username, i.username))
        return l

    seller = forms.ChoiceField(required=False, choices=sellers_cj())
    action = forms.ChoiceField(required=False, choices=[(None,"--------"), (0,"Disable ⛔"), (1 , "Enable ✅")])

    def clean(self):
        action = self.cleaned_data.get('action')
        seller = self.cleaned_data.get('seller')

        if seller == "" or action == "":
            raise ValidationError("انتخاب کنید.")

class ChangeInfiniteLimirForm(forms.Form):
    usage_limit = forms.IntegerField(required=False, min_value=0, max_value=10000)

    # def clean_usage_limit(self):
    #     usage_limit = self.cleaned_data.get('usage_limit')
    #
    #     return self.cleaned_data.get('usage_limit')
