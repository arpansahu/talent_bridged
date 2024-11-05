import ssl

from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views import View
from django.views.decorators.csrf import csrf_protect
from django.views.generic import FormView, RedirectView
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, UpdateView, DetailView, CreateView, FormView
from account.forms import RegistrationForm, AccountAuthenticationForm, AccountUpdateForm, PasswordResetForm, LoginForm, ResendActivationEmailForm
from django.conf import settings
from django.contrib.auth.views import PasswordContextMixin

from account.models import Account, MyAccountManager
from account.token import account_activation_token
from django.utils import timezone


from mailjet_rest import Client

mailjet = Client(auth=(settings.MAIL_JET_API_KEY, settings.MAIL_JET_API_SECRET), version='v3.1')


class CustomPasswordResetView(PasswordContextMixin, FormView):
    email_template_name = "registration/password_reset_email.html"
    form_class = PasswordResetForm
    from_email = None
    html_email_template_name = "registration/password_reset_email.html"
    subject_template_name = "registration/password_reset_subject.txt"
    success_url = reverse_lazy("password_reset_done")
    template_name = "registration/password_reset_form.html"
    token_generator = default_token_generator
    title = _("Password Reset")

    @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        email = form.cleaned_data.get("email")
        try:
            user = Account.objects.get(email=email)

            if not user.is_active:
                messages.warning(self.request, "Your account is not active. Please activate it using the link sent to your email.")
                return super().form_invalid(form)

            scheme = 'https' if self.request.headers.get('X-Forwarded-Proto') == 'https' else 'http'
            host = self.request.get_host()
            self.extra_email_context = {
                "date": timezone.now().strftime('%d %b, %Y'),
                "protocol": scheme,
                "domain": host,
            }

            opts = {
                "use_https": self.request.is_secure(),
                "token_generator": self.token_generator,
                "from_email": self.from_email,
                "email_template_name": self.email_template_name,
                "subject_template_name": self.subject_template_name,
                "html_email_template_name": self.html_email_template_name,
                "request": self.request,
                "extra_email_context": self.extra_email_context,
            }

            try:
                # raise Exception("Simulated error before saving form.")
                form.save(**opts)
                messages.success(self.request, "Password reset email has been sent successfully.")
            except Exception as e:
                # logger.error(f"Failed to send password reset email: {e}")
                messages.error(self.request, "There was an error sending the password reset email. Please try again later.")

        except Account.DoesNotExist:
            messages.info(self.request, "If an account with this email exists, you should receive an email shortly.")

        return super().form_valid(form)


def send_mail_account_activate(reciever_email, user, request, SUBJECT="Confirm Your Email"):
    scheme = 'https' if request.headers.get('X-Forwarded-Proto') == 'https' else 'http'
    host = request.get_host()
    # Render the account activation email template
    message = render_to_string('emails/email_account_activate.html', {
        'user': user,
        'protocol': scheme,
        'domain': host,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
        'date': timezone.now().strftime('%d %b, %Y'),
    })

    data = {
        'Messages': [
            {
                "From": {
                    "Email": settings.MAIL_JET_VERIFICATION_EMAIL,
                    "Name": "Talent Bridged"
                },
                "To": [
                    {
                        "Email": reciever_email,
                        "Name": user.username or "User"
                    }
                ],
                "Subject": SUBJECT,
                "HTMLPart": message,  # Using the rendered HTML message here
                "CustomID": f"ActivationEmail-{reciever_email}"
            }
        ]
    }

    # Instantiate Mailjet client
    mailjet = Client(auth=(settings.MAIL_JET_API_KEY, settings.MAIL_JET_API_SECRET), version='v3.1')

    # Send email through Mailjet
    result = mailjet.send.create(data=data)
    print("Account activation email sent")
    return result


def activate(request, uidb64, token):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        return render(request, 'account/account_activation_done.html', context={'message': 'Thank you for your email '
                                                                                           'confirmation. Now you can '
                                                                                           'login your account.'})
    else:
        return render(request, 'account/account_activation_done.html', context={'message': 'Activation link is invalid!'})


class RegistrationView(View):
    def get(self, request, *args, **kwargs):
        
        if request.user.is_authenticated:
            return render(request, 'account/already_logged_in.html', {
                'message': 'You are already logged in. Please log out before creating a new account.'
            })

        context = {}
        form = RegistrationForm()
        context['registration_form'] = form
        return render(request, 'account/register.html', context)

    def post(self, request, *args, **kwargs):
        context = {}
        form = RegistrationForm(request.POST)
        if form.is_valid():
            account = form.save()

            # Link free subscriptions to the newly created user
            account_manager = MyAccountManager()
            account_manager.link_free_subscriptions(account)

            email = form.cleaned_data.get('email')
            send_mail_account_activate(email, account, request)
            return render(request, 'account/account_activation_done.html', {'message': 'Check your mail and activate your account'})
        else:
            context['registration_form'] = form
        return render(request, 'account/register.html', context)


@method_decorator(login_required(redirect_field_name=''), name='dispatch')
class LogoutView(RedirectView):

    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect('home')


class LoginView(View):
    def get(self, request):
        form = LoginForm()
        msg = None
        if request.user.is_authenticated:
            return redirect('home')
        return render(request, "account/login.html", {"form": form, "msg": msg})

    def post(self, request):
        form = LoginForm(request.POST or None)
        msg = None

        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")

            try:
                # Attempt to fetch the user by email
                user = Account.objects.get(email=username)
                
                # Check if the user's password is valid
                if user.check_password(password):
                    # If the password is correct, check if the account is active
                    if user.is_active:
                        login(request, user)
                        return redirect("admin-home")
                    else:
                        msg = "Your account is not active. Please activate it using the link sent to your email."
                else:
                    msg = "Invalid credentials. Please check your username and password."
            except Account.DoesNotExist:
                msg = "Invalid credentials. Please check your username and password."

        else:
            msg = "Error validating the form."

        return render(request, "account/login.html", {"form": form, "msg": msg})




@method_decorator(login_required(redirect_field_name=''), name='dispatch')
class AccountView(View):
    def get(self, request, *args, **kwargs):
        context = {}
        form = AccountUpdateForm(
            initial={
                "email": request.user.email,
                "username": request.user.username,
                "name": request.user.name
            }
        )
        context["account"] = Account.objects.get(email=request.user.email)
        context['account_form'] = form
        return render(request, 'account/account.html', context)

    def post(self, request, *args, **kwargs):
        context = {}
        form = AccountUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            print(form.__dict__)
            form.save()

        context["account"] = Account.objects.get(email=request.user.email)
        context['account_form'] = form
        return render(request, 'account/account.html', context)


from django.contrib import messages


class ResendActivationEmailView(View):
    def get(self, request):
        form = ResendActivationEmailForm()
        return render(request, "account/resend_activation_email.html", {"form": form})

    def post(self, request):
        form = ResendActivationEmailForm(request.POST)
        
        if form.is_valid():
            email = form.cleaned_data.get("email")
            try:
                user = Account.objects.get(email=email)

                if user.is_active:
                    messages.info(request, "This account is already active. You can log in directly.")
                    return redirect("login")
                else:
                    # Send activation email
                    send_mail_account_activate(reciever_email=email, user=user, request=request)
                    messages.success(request, "An activation email has been sent. Please check your inbox.")
            
            except Account.DoesNotExist:
                messages.error(request, "No account found with this email address.")
                return redirect("resend_activation_email")

        return render(request, "account/resend_activation_email.html", {"form": form})


def error_404(request, exception):
    return render(request, 'error/error_404.html')


def error_400(request, exception):
    return render(request, 'error/error_400.html')


def error_403(request, exception):
    return render(request, 'error/error_403.html')


def error_500(request):
    return render(request, 'error/error_500.html')