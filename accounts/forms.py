from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError
import json
from .models import User
# from sellers_connection.models import Bots


class UserCreationForm(forms.ModelForm):
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='confirm Password', widget=forms.PasswordInput)


    class Meta:
        model = User
        fields = ['username', 'password', "password2", "level_access"]

    def clean_password2(self):
        cd = self.cleaned_data
        if cd["password"] and cd["password2"] and cd['password'] != cd['password2']:
            raise forms.ValidationError("Passwords must match")
        return cd["password2"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(help_text="<a href=\"../password/\">change password</a>")
    class Meta:
        model = User
        fields = ['username', "password", "level_access"]


class LoginForm(forms.Form):
    username = forms.CharField(label="یوزرنیم:")
    password = forms.CharField(widget=forms.PasswordInput(), label="رمز عبور:")

    def clean(self):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")
        user = authenticate(username=username, password=password)
        if user is None:
            raise ValidationError("یوزرنیم یا پسوورد اشتباه است.")



class AddUserForm(forms.Form):
    username = forms.CharField(max_length=25)
    password = forms.CharField()
    password2 = forms.CharField()

    def clean(self):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")
        password2 = self.cleaned_data.get("password2")
        if " " in username or " " in password:
            raise ValidationError("username or password can not contain space.")

        if not username and not password and not password2:
            raise ValidationError("enter username and password")

        if password != password2:
            raise ValidationError("Passwords must match")

        if User.objects.filter(username=username).exists():
            raise ValidationError("Username already exists")



class ChangeSettingForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        with open("settings.json", "r", encoding="utf-8") as f:
            j = json.load(f)
        self.fields["card_number"].initial = j["pay_card_number"]
        self.fields["card_name"].initial = j["pay_card_name"]
        self.fields["prices_msg_id"].initial = j["prices_msg_id"]
        self.fields["U1_1M"].initial = j["unlimit_limit"]["1u"]["1m"]
        self.fields["U1_2M"].initial = j["unlimit_limit"]["1u"]["2m"]
        self.fields["U1_3M"].initial = j["unlimit_limit"]["1u"]["3m"]
        self.fields["U2_1M"].initial = j["unlimit_limit"]["2u"]["1m"]
        self.fields["U2_2M"].initial = j["unlimit_limit"]["2u"]["2m"]
        self.fields["U2_3M"].initial = j["unlimit_limit"]["2u"]["3m"]
        self.fields["config_name_counter"].initial = j["config_name_counter"]


    card_number = forms.IntegerField()
    card_name = forms.CharField(max_length=25)
    prices_msg_id = forms.IntegerField()
    U1_1M = forms.IntegerField()
    U1_2M = forms.IntegerField()
    U1_3M = forms.IntegerField()
    U2_1M = forms.IntegerField()
    U2_2M = forms.IntegerField()
    U2_3M = forms.IntegerField()
    config_name_counter = forms.IntegerField()


    def clean_card_number(self):
        card_number = self.cleaned_data["card_number"]
        if len(str(card_number)) != 16:
            raise ValidationError("شماره کارت باید 16 رقمی باشد.")
        return card_number

    def clean_config_name_counter(self):
        config_name_counter = self.cleaned_data["config_name_counter"]
        with open("settings.json", "r", encoding="utf-8") as f:
            last = json.load(f)["config_name_counter"]
            if config_name_counter > last:
                return config_name_counter
            else:
                return last + 1


class VpnAppsForm(forms.Form):
    app_name = forms.CharField(max_length=25,required=False)
    download_url = forms.URLField(required=False)
    guid = forms.IntegerField(required=False)
