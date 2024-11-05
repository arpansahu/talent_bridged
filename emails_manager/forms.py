from django import forms
from django.core.validators import RegexValidator

class ContactForm(forms.Form):
    name = forms.CharField(
        widget=forms.TextInput(attrs={'class': "form-control", 'placeholder': "Your name"})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': "form-control", 'placeholder': "Your email"})
    )
    subject = forms.CharField(
        widget=forms.TextInput(attrs={'class': "form-control", 'placeholder': "Your subject"})
    )
    contact = forms.CharField(
        validators=[
            RegexValidator(
                regex=r'^\+\d{1,3} \d{6,14}$',
                message="Enter a valid phone number in the format '+00 123456789', including the country code."
            )
        ],
        widget=forms.TextInput(attrs={'class': "form-control", 'placeholder': "+00 123456789"})
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={'class': "form-control", "rows": 5, 'placeholder': "Enter your message..."})
    )
