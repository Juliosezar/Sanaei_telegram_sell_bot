from django import forms

class SearchCustomerForm(forms.Form):
    search_user = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'placeholder': 'Search Userid or Username'}))


class ChangeWalletForm(forms.Form):
    wallet = forms.IntegerField(max_value=999,min_value=0)