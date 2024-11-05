from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

from jobs.models import Jobs
from skills.models import Skills

User = get_user_model()
from django.contrib.auth import authenticate, get_user_model
from django import forms
from companies.models import Company
from django.forms import TextInput, NumberInput, ClearableFileInput, FileInput


class LoginForm(forms.Form):
    username = forms.CharField(
        error_messages={
            'required': "Please Enter your Email"
        },
        widget=forms.TextInput(
            attrs={
                "placeholder": "Username",
                "class": "form-control"

            }
        ))
    password = forms.CharField(
        error_messages={
            'required': "Please Enter your Password"
        },
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Password",
                "class": "form-control"
            }
        ))



class ModifyCompaniesForm(forms.ModelForm):
    # logo = forms.FileField(widget=forms.FileInput)
    logo = forms.ImageField(label='Company Logo', required=False, error_messages={'invalid': "Image files only"},
                            widget=forms.FileInput(attrs={'class': 'form-control', 'id': 'logo-input', 'onchange':
                                "upload_img(this);"}))

    class Meta:
        model = Company
        fields = (
            'name',
            'career_page',
            'job_openings',
            'logo'
        )

        widgets = {
            'name': TextInput(attrs={'class': 'form-control'}),
            'career_page': TextInput(attrs={'class': 'form-control'}),
            'job_openings': NumberInput(attrs={'class': 'form-control'}),
            # 'logo': ClearableFileInput(attrs={'class': 'form-control'}),
        }
