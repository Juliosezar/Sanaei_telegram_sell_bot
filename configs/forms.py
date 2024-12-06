from django import forms

class SearchConfigForm(forms.Form):
    search_config = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'placeholder': 'Search Config Name or UUID'}))
