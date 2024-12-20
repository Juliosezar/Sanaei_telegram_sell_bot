from email.policy import default

from django import forms
from django.core.exceptions import ValidationError


class ChangeSellerAccessForm(forms.Form):
    level_access = forms.ChoiceField(choices=[(0,"معمولی"), (1, "با زیرمجموعه")], required=False)
    payment_limit = forms.IntegerField(required=False, min_value=0, initial=0)
    finance_access = forms.BooleanField(required=False, initial=True)
    create_config_acc = forms.BooleanField(required=False, initial=True)
    list_configs_acc = forms.BooleanField(required=False, initial=True)
    delete_config_acc = forms.BooleanField(required=False, initial=True)
    disable_config_acc = forms.BooleanField(required=False, initial=True)
    bot = forms.ChoiceField(choices=[],required=False)

    def clean(self):
        payment_limit = self.cleaned_data.get('payment_limit')
        print(payment_limit)
        if not 0 <= payment_limit or not  payment_limit <= 99000:
            raise ValidationError("محدودیت خرید باید بین 0 تا 99000 هزار تومان باشد.")
