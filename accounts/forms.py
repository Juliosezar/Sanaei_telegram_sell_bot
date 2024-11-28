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


