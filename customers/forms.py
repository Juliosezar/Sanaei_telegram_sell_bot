from django import forms

class SearchCustomerForm(forms.Form):
    search_user = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'placeholder': 'Search Userid or Username'}))


class ChangeWalletForm(forms.Form):
    wallet = forms.IntegerField(max_value=999,min_value=0)

class SendMessageToAllForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea, required=True)

    def clean_message(self):
        message = self.cleaned_data['message']
        if len(message) < 2:
            raise forms.ValidationError("Message is too short")
        return message
