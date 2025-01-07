from os import environ

from django import forms
from django.core.exceptions import ValidationError


class SearchCustomerForm(forms.Form):
    search_user = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'placeholder': 'Search Userid or Username'}))


class ChangeWalletForm(forms.Form):
    wallet = forms.IntegerField(max_value=999,min_value=0)


class SendMessageToCustomerForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea, required=True)

    def clean_message(self):
        message = self.cleaned_data['message']
        if len(message) < 2:
            raise forms.ValidationError("Message is too short")
        return message



class SendMessageToAllForm(forms.Form):
    message = forms.CharField()

    def clean_message(self):
        side_channel = environ.get("SIDE_CHANNEL_USERNAME").replace("@","")
        message = self.cleaned_data['message']
        if not side_channel in message:
            raise ValidationError("پیام باید از کانال تعیین شده باشد.")
        if not message.startswith("https://t.me/"):
            raise ValidationError("لینک پیام را کپی و وارد کنید.")
        return message