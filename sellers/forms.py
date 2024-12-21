from email.policy import default
from accounts.models import User
from django import forms
from django.core.exceptions import ValidationError


class ChangeSellerAccessForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.seller = User.objects.get(username=kwargs.pop('username', None))
        super().__init__(*args, **kwargs)

        self.fields["level_access"].initial = self.seller.level_access
        self.fields["payment_limit"].initial = self.seller.payment_limit
        self.fields["finance_access"].initial = self.seller.finance_access
        self.fields["create_config_acc"].initial = self.seller.create_config_acc
        self.fields["list_configs_acc"].initial = self.seller.list_configs_acc
        self.fields["delete_config_acc"].initial = self.seller.delete_config_acc
        self.fields["disable_config_acc"].initial = self.seller.disable_config_acc
        self.fields["bot"].initial = self.seller.bot
        self.fields["brand"].initial = self.seller.brand


    level_access = forms.ChoiceField(choices=[(0,"معمولی"), (1, "با زیرمجموعه")], required=False,)
    payment_limit = forms.IntegerField(required=False, min_value=0)
    finance_access = forms.BooleanField(required=False)
    create_config_acc = forms.BooleanField(required=False)
    list_configs_acc = forms.BooleanField(required=False)
    delete_config_acc = forms.BooleanField(required=False)
    disable_config_acc = forms.BooleanField(required=False)
    bot = forms.ChoiceField(choices=[],required=False)
    brand = forms.CharField(required=False)

    def clean(self):
        payment_limit = self.cleaned_data.get('payment_limit')
        print(payment_limit)
        if not 0 <= payment_limit or not  payment_limit <= 99000:
            raise ValidationError("محدودیت خرید باید بین 0 تا 99000 هزار تومان باشد.")
