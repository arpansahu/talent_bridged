from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from django.conf.urls.static import static
from django.conf import settings
import time
import sys
from django.urls import re_path
from account.views import (
    CustomPasswordResetView,
    LogoutView,
    LoginView,
    AccountView,
#     AccountUpdateView,
    RegistrationView,
    activate,
    ResendActivationEmailView
)

from .views import (
     home_view,
     terms_and_condition_view,
     privacy_policy_view,
     data_protection_policy_view,
     data_processing_agreement_view,
     affiliate_program_view,
     proxy_aggregator_view
)

from emails_manager.views import (
     contact_view,
     get_otp_view,
)



def trigger_error(request):
    division_by_zero = 1 / 0

def large_resource(request):
   time.sleep(4)
   return HttpResponse("Done!")

urlpatterns = [
    # Admin URL
    path('django-admin/', admin.site.urls, name='admin'),

    # Dashboard Views
    path('', home_view, name='home'),

    path('home/', include('admin_panel.urls')),


    path('contact/', contact_view, name='contact'),
    path('get-otp', get_otp_view, name='get-otp'),

    # Extra Information View
    path('terms-and-conditions/', terms_and_condition_view, name='terms_and_conditions'),
    path('privacy-policy/', privacy_policy_view, name='privacy_policy'),
    path('data-protection-policy/', data_protection_policy_view, name='data_protection_policy'),
    path('data-protection-policy/', data_processing_agreement_view, name='data_processing_agreement'),
    path('affiliate-program/', affiliate_program_view, name='affiliate_program'),
    path('proxy-aggregator-view/', proxy_aggregator_view, name='proxy_aggregator_view'),

    path('support/',contact_view  , name='support'),

    #Auth Views
    path('register/', RegistrationView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('login/', LoginView.as_view(), name='login'),
    path('account/', AccountView.as_view(), name='account'),
    
#     path('account/<pk>/update', AccountUpdateView.as_view(), name='account_update'),
    re_path(r'activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,40})/', 
            activate, name='account_activate'),
    path('password_change/done/',
         auth_views.PasswordChangeDoneView.as_view(template_name='registration/password_change_done.html'),
         name='password_change_done'),

    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='registration/password_change.html'),
         name='password_change'),

    path('password_reset/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_done.html'),
         name='password_reset_done'),

    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_change.html'),
         name='password_reset_confirm'),

    path('password_reset/', CustomPasswordResetView.as_view(), name='password_reset'),

    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'),
         name='password_reset_complete'),
         
    path("resend-activation-email/", ResendActivationEmailView.as_view(), name="resend_activation_email"),


    #sentry test view 
    path('sentry-debug/', trigger_error),
    path('large_resource/', large_resource)
] 

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'account.views.error_404'
handler500 = 'account.views.error_500'
handler403 = 'account.views.error_403'
handler400 = 'account.views.error_400'

# Check if the current command is not related to migrations
# if 'migrate' not in sys.argv and 'makemigrations' not in sys.argv:
#     # Only call this function if it's not during migrations
#     start_initial_proxies()