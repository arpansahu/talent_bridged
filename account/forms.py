from django import forms
from django.contrib.auth.forms import UserCreationForm, _unicode_ci_compare, UserChangeForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from account.models import Account
from django.contrib.auth import authenticate, get_user_model, password_validation
from django.utils.translation import gettext_lazy as _
from django.template import loader
from django.core.validators import EmailValidator

UserModel = get_user_model()

from django.conf import settings
from mailjet_rest import Client

# Django Admin forms

class CustomAccountCreationForm(UserCreationForm):
    class Meta:
        model = Account
        fields = ('email', 'username', 'name', 'password1', 'password2', 'profile_photo')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Example: Add custom CSS classes to fields
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['username']
        if commit:
            user.save()
        return user

class CustomAccountUpdateForm(UserChangeForm):
    class Meta:
        model = Account
        fields = ('email', 'username', 'is_active', 'is_staff', 'is_admin', 'profile_photo', 'name')

    # Override the __init__ method to customize the form if needed
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Example: Add custom CSS classes to fields
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        # Add additional customizations here

class LoginForm(forms.Form):
    username = forms.EmailField(
        error_messages={
            'required': "Please Enter your Email",
            'invalid': "Enter a valid email address"
        },
        widget=forms.EmailInput(
            attrs={
                "placeholder": "Email",
                "class": "form-control"
            }
        ),
        validators=[EmailValidator()]
    )
    password = forms.CharField(
        error_messages={
            'required': "Please Enter your Password"
        },
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Password",
                "class": "form-control"
            }
        )
    )


class RegistrationForm(UserCreationForm):
    username = forms.CharField(
        error_messages={
            'required': "Please Enter your Username"
        },
        widget=forms.TextInput(
            attrs={
                "placeholder": "Username",
                "class": "form-control"

            }
        ))

    password1 = forms.CharField(
        error_messages={
            'required': "Please Enter your Password"
        },
        label=_("Password"),
        help_text=password_validation.password_validators_help_text_html(),
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Password1",
                "class": "form-control",
                "autocomplete": "new-password"
            }
        ))

    password2 = forms.CharField(
        error_messages={
            'required': "Please Enter your Password Again"
        },
        label=_("Password confirmation"),
        help_text=_("Enter the same password as before, for verification."),
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Password2",
                "class": "form-control",
                "autocomplete": "new-password"
            }
        ))

    email = forms.EmailField(
        max_length=60,
        help_text='Required. Add a valid email',
        widget=forms.EmailInput(
            attrs={
                "placeholder": "Email",
                "class": "form-control"
            }
        )
    )

    class Meta:
        model = Account
        fields = ("email", "username", "password1", "password2")


class AccountAuthenticationForm(forms.ModelForm):
    password = forms.CharField(label='Password', widget=forms.PasswordInput)

    class Meta:
        model = Account
        fields = ("email", "password")

    def clean(self):
        if self.is_valid():
            email = self.cleaned_data['email']
            password = self.cleaned_data['password']

            if not authenticate(email=email, password=password):
                raise forms.ValidationError("Invalid Credentials")


class AccountUpdateForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ('email', 'username', 'profile_photo', 'name')
        widgets = {
            'email': forms.TextInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_photo': forms.FileInput(attrs={'class': 'form-control'})
        }

    def clean_email(self):
        if self.is_valid():
            email = self.cleaned_data['email']
            try:
                account = Account.objects.exclude(pk=self.instance.pk).get(email=email)
            except Account.DoesNotExist:
                return email
            raise forms.ValidationError('Email "%s" is already in use.' % email)

    def clean_username(self):
        if self.is_valid():
            username = self.cleaned_data['username']
            try:
                account = Account.objects.exclude(pk=self.instance.pk).get(username=username)
            except Account.DoesNotExist:
                return username


class PasswordResetForm(forms.Form):
    email = forms.EmailField(
        label=_("Email"),
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )

    def send_mail(
            self,
            subject_template_name,
            email_template_name,
            context,
            from_email,
            to_email,
            html_email_template_name=None,
            user=None
    ):
        """
        Send a django.core.mail.EmailMultiAlternatives to `to_email`.
        """
        subject = loader.render_to_string(subject_template_name, context)
        # Email subject *must not* contain newlines
        subject = "".join(subject.splitlines())
        body = loader.render_to_string(email_template_name, context)

        if html_email_template_name is not None:
            html_email = loader.render_to_string(html_email_template_name, context)

        mailjet = Client(auth=(settings.MAIL_JET_API_KEY, settings.MAIL_JET_API_SECRET), version='v3.1')
        data = {
            'Messages': [
                {
                    "From": {
                        "Email": settings.MAIL_JET_VERIFICATION_EMAIL,
                        "Name": "Talent Bridged"
                    },
                    "To": [
                        {
                            "Email": to_email,
                            "Name": user.username
                        }
                    ],
                    "Subject": subject,
                    "TextPart": body,
                    "HTMLPart": body,
                    "CustomID": f"{user.email}"
                }
            ]
        }
        result = mailjet.send.create(data=data)
        if result:
            print(f"Mail Send Successfully {result}")
        else:
            print(f"Mail Send Failed {result}")

    def get_users(self, email):
        """Given an email, return matching user(s) who should receive a reset.

        This allows subclasses to more easily customize the default policies
        that prevent inactive users and users with unusable passwords from
        resetting their password.
        """
        email_field_name = UserModel.get_email_field_name()
        active_users = UserModel._default_manager.filter(
            **{
                "%s__iexact" % email_field_name: email,
                "is_active": True,
            }
        )
        return (
            u
            for u in active_users
            if u.has_usable_password()
               and _unicode_ci_compare(email, getattr(u, email_field_name))
        )

    def save(
            self,
            domain_override=None,
            subject_template_name="registration/password_reset_subject.txt",
            email_template_name="registration/password_reset_email.html",
            use_https=False,
            token_generator=default_token_generator,
            from_email=None,
            request=None,
            html_email_template_name=None,
            extra_email_context=None,
    ):
        """
        Generate a one-use only link for resetting password and send it to the
        user.
        """
        email = self.cleaned_data["email"]
        if not domain_override:
            current_site = get_current_site(request)
            site_name = current_site.name
            domain = current_site.domain
        else:
            site_name = domain = domain_override
        email_field_name = UserModel.get_email_field_name()
        for user in self.get_users(email):
            user_email = getattr(user, email_field_name)
            context = {
                "email": user_email,
                "domain": domain,
                "site_name": site_name,
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "user": user,
                "token": token_generator.make_token(user),
                "protocol": "https" if use_https else "http",
                **(extra_email_context or {}),
            }
            self.send_mail(
                subject_template_name,
                email_template_name,
                context,
                from_email,
                user_email,
                html_email_template_name=html_email_template_name,
                user=user
            )


class ResendActivationEmailForm(forms.Form):
    email = forms.EmailField(label="Enter your account email" ,max_length=254, widget=forms.EmailInput(attrs={"autocomplete": "email", "class": "form-control"}))

