from django.shortcuts import render
from api.models import APIRequestLog
from account.models import AccountOrders
from payment.models import SubscriptionItem
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
import base64
import pyotp
import traceback
from mailjet_rest import Client  # Import Mailjet client
from datetime import datetime
import random


# Set up logging
import logging
logger = logging.getLogger('django')


@login_required
def dashboard_view(request):
    # Log the start of the dashboard view
    # logger.info(f"Dashboard view accessed by user: {request.user.email}")

    # Get the active API key for the user (assuming one active API key per user)
    api_key = request.user.api_key  # Access the API key through the related ForeignKey on the Account model

    if api_key is None or not api_key.is_active:
        # logger.warning(f"No active API key found for user: {request.user.email}")

        # No API key found or it is inactive, return empty data for last 7 days
        last_7_days = []
        today = timezone.now().date()
        tomorrow = today + timedelta(days=1)

        for i in range(7):
            day = tomorrow - timedelta(days=i)
            day_data = {
                'date': day.strftime('%a, %d %b'),
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'success_rate': 0,
                'api_credits_used': 0
            }
            last_7_days.append(day_data)

        last_7_days.reverse()

        # logger.info(f"Returning empty stats for user {request.user.email}")

        total_requests = 0,
        successful_requests = 0,
        failed_requests = 0,
        success_rate = 0,
        api_credits_used = 0,
        logs = [],
        last_7_days = last_7_days
       

    else:
        # Log API key status
        # logger.info(f"Active API key found for user: {request.user.email}")

        # If API key is present and active, calculate stats
        logs = APIRequestLog.objects.filter(api_key=api_key)

        # Calculate overall stats for the dashboard
        total_requests = logs.count()
        successful_requests = logs.filter(status=200).count()
        failed_requests = total_requests - successful_requests
        success_rate = (successful_requests / total_requests) * 100 if total_requests > 0 else 0

        # logger.info(f"Calculated stats for user {request.user.email}: total_requests={total_requests}, success_rate={success_rate:.2f}%")

        # Calculate stats for the last 7 days (including today and tomorrow)
        today = timezone.now().date()
        tomorrow = today + timedelta(days=1)

        last_7_days = []

        for i in range(7):
            day = tomorrow - timedelta(days=i)
            day_logs = logs.filter(time__date=day)

            total_requests_day = day_logs.count()
            successful_requests_day = day_logs.filter(status=200).count()
            failed_requests_day = total_requests_day - successful_requests_day
            success_rate_day = (successful_requests_day / total_requests_day * 100) if total_requests_day > 0 else 0
            api_credits_used_day = sum(log.api_credits for log in day_logs)

            day_data = {
                'date': day.strftime('%a, %d %b'),
                'total_requests': total_requests_day,
                'successful_requests': successful_requests_day,
                'failed_requests': failed_requests_day,
                'success_rate': success_rate_day,
                'api_credits_used': api_credits_used_day,
            }
            last_7_days.append(day_data)

        last_7_days.reverse()

    # Log subscription checks
    # logger.info(f"Fetching active subscriptions for user: {request.user.email}")

    # Get Current Active Subscription for Proxy Aggregator using request.user and the service_name 'proxy_aggregator'
    active_order_proxy_aggregator = AccountOrders.objects.filter(
        account=request.user, 
        order__subscription_item__service_name='proxy_aggregator',
        is_active=True
    ).select_related('order__subscription_item').first()

    # if active_order_proxy_aggregator:
    #     logger.info(f"Active 'proxy_aggregator' subscription found for user {request.user.email}")
    # else:
    #     logger.warning(f"No active 'proxy_aggregator' subscription found for user {request.user.email}")

    active_order_proxy_concurrency = AccountOrders.objects.filter(
        account=request.user, 
        order__subscription_item__service_name='proxy_concurrency',
        is_active=True
    ).select_related('order__subscription_item').first()

    # if active_order_proxy_concurrency:
    #     logger.info(f"Active 'proxy_concurrency' subscription found for user {request.user.email}")
    # else:
    #     logger.warning(f"No active 'proxy_concurrency' subscription found for user {request.user.email}")

    # Check if active subscriptions exist and fetch their limits
    if active_order_proxy_aggregator:
        subscription_limit_gb = active_order_proxy_aggregator.order.subscription_item.monthly_limit_gb
        subscription_limit_requests = active_order_proxy_aggregator.order.subscription_item.monthly_request_limit
    else:
        subscription_limit_gb = 0
        subscription_limit_requests = 0

    if active_order_proxy_concurrency:
        subscription_limit_concurrency = active_order_proxy_concurrency.order.subscription_item.concurrent_threads
    else:
        subscription_limit_concurrency = 0

    # Log available plans
    # logger.info(f"Fetching available plans for 'proxy_aggregator' and 'proxy_concurrency' for user {request.user.email}")
    
    proxy_aggregator_plans = SubscriptionItem.objects.filter(service_name='proxy_aggregator').exclude(subscription_type='Free').order_by('price_in_usd')
    proxy_concurrency_plans = SubscriptionItem.objects.filter(service_name='proxy_concurrency').exclude(subscription_type='Free').order_by('price_in_usd')

    # Determine the current plan type message
    if active_order_proxy_aggregator and active_order_proxy_aggregator.order.subscription_item.subscription_type == 'Free' and active_order_proxy_concurrency and active_order_proxy_concurrency.order.subscription_item.subscription_type == 'Free':
        plan_type_message = 'Free Plan'
    else:
        plan_type_message = 'Premium Plan'

    # Get the current billing address for the user, if it exists
    billing_address = request.user.address if request.user.address else None

    # Log the context data that will be passed to the template
    # logger.info(f"Rendering dashboard for user {request.user.email} with context: total_requests={total_requests}, plan_type_message={plan_type_message}")

    context = {
        'total_requests': total_requests,
        'successful_requests': successful_requests,
        'failed_requests': failed_requests,
        'success_rate': success_rate,
        'logs': logs,
        'last_7_days': last_7_days,
        'subscription_limit_gb': subscription_limit_gb,
        'subscription_limit_requests': subscription_limit_requests,
        'proxy_aggregator_plans': proxy_aggregator_plans,
        'proxy_concurrency_plans': proxy_concurrency_plans,
        'proxy_aggregator_subscription': active_order_proxy_aggregator,
        'proxy_concurrency_subscription': active_order_proxy_concurrency,
        'billing_address': billing_address,
        'active_concurrency': api_key.requests_in_progress if api_key else 0,
        'subscription_limit_concurrency': subscription_limit_concurrency,
        'plan_type_message': plan_type_message
    }

    # Log before rendering the template
    # logger.info(f"Rendering dashboard template for user {request.user.email}")
    
    return render(request, 'dashboard/home.html', context)

def request_viewer(request):
    request_logs = APIRequestLog.objects.all().order_by('-created_at')
    paginator = Paginator(request_logs, 10)  # Show 10 requests per page

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj
    }
    return render(request, 'request_viewer.html', context)

def ajax_request_viewer(request):
    domain = request.GET.get('domain', '')
    latency = request.GET.get('latency', '')
    api_credits = request.GET.get('apiCredits', '')
    status = request.GET.get('status', '')
    method = request.GET.get('method', '')
    page = request.GET.get('page', 1)  # Get the current page number from the query parameters
    items_per_page = 10  # Set how many items per page

    request_logs = APIRequestLog.objects.all()

    # Apply filters
    if domain:
        request_logs = request_logs.filter(domain__icontains=domain)
    if latency:
        request_logs = request_logs.filter(latency__gte=latency)
    if api_credits:
        request_logs = request_logs.filter(api_credits__gte=api_credits)
    if status:
        request_logs = request_logs.filter(status=status)
    if method:
        request_logs = request_logs.filter(method=method)

    # Paginate the queryset
    paginator = Paginator(request_logs, items_per_page)
    paginated_logs = paginator.get_page(page)

    # Prepare the response data
    data = [
        {
            'domain': log.domain,
            'url': log.url,
            'method': log.method,
            'status': log.status,
            'latency': log.latency,
            'time': log.created,
            'api_credits': log.api_credits,
            'is_premium': 'Yes' if log.is_premium else 'No',
            'request_data': log.request_data
        }
        for log in paginated_logs
    ]

    # Include pagination information
    response = {
        'data': data,
        'total_pages': paginator.num_pages,
        'current_page': paginated_logs.number
    }

    return JsonResponse(response, safe=False)

def terms_and_condition_view(request):
    return render(request, 'extras/terms_and_conditions.html')

def privacy_policy_view(request):
    return render(request, 'extras/privacy_policy.html')

def data_protection_policy_view(request):
    return render(request, 'extras/data_protection_policy.html')

def data_processing_agreement_view(request):
    return render(request, 'extras/data_processing_agreement.html')

def affiliate_program_view(request):
    return render(request, 'extras/coming_soon.html')

def home_view(request):
    return render(request, 'home.html')


def proxy_aggregator_view(request):
    # Full list of countries by continent
    continents = {
        'Africa': [('dz', 'Algeria'), ('ao', 'Angola'), ('bw', 'Botswana'), ('eg', 'Egypt'), ('gh', 'Ghana'), ('ke', 'Kenya'), 
                   ('za', 'South Africa'), ('ng', 'Nigeria'), ('cm', 'Cameroon'), ('ma', 'Morocco'), ('sn', 'Senegal'), ('tn', 'Tunisia'), 
                   ('ci', 'Ivory Coast'), ('mg', 'Madagascar'), ('et', 'Ethiopia'), ('ug', 'Uganda')],
        
        'Asia': [('cn', 'China'), ('in', 'India'), ('jp', 'Japan'), ('kr', 'South Korea'), ('ru', 'Russia'), ('sa', 'Saudi Arabia'), 
                 ('th', 'Thailand'), ('vn', 'Vietnam'), ('sg', 'Singapore'), ('my', 'Malaysia'), ('id', 'Indonesia'), ('ph', 'Philippines'),
                 ('iq', 'Iraq'), ('ir', 'Iran'), ('ae', 'United Arab Emirates'), ('kw', 'Kuwait')],
        
        'Europe': [('fr', 'France'), ('de', 'Germany'), ('it', 'Italy'), ('gb', 'United Kingdom'), ('es', 'Spain'), ('se', 'Sweden'), 
                   ('ch', 'Switzerland'), ('nl', 'Netherlands'), ('be', 'Belgium'), ('pl', 'Poland'), ('pt', 'Portugal'), ('gr', 'Greece'),
                   ('no', 'Norway'), ('fi', 'Finland'), ('ie', 'Ireland'), ('dk', 'Denmark')],
        
        'North America': [('ca', 'Canada'), ('mx', 'Mexico'), ('us', 'United States'), ('gt', 'Guatemala'), ('pa', 'Panama'), ('cu', 'Cuba'), 
                          ('hn', 'Honduras'), ('cr', 'Costa Rica'), ('jm', 'Jamaica'), ('tt', 'Trinidad and Tobago'), ('bs', 'Bahamas'), 
                          ('bz', 'Belize')],
        
        'South America': [('ar', 'Argentina'), ('br', 'Brazil'), ('cl', 'Chile'), ('co', 'Colombia'), ('py', 'Paraguay'), ('uy', 'Uruguay'), 
                          ('pe', 'Peru'), ('ve', 'Venezuela'), ('bo', 'Bolivia'), ('ec', 'Ecuador'), ('gy', 'Guyana'), ('sr', 'Suriname')],
        
        'Oceania': [('au', 'Australia'), ('nz', 'New Zealand'), ('fj', 'Fiji'), ('pg', 'Papua New Guinea'), ('vu', 'Vanuatu'), 
                    ('ws', 'Samoa'), ('tv', 'Tuvalu'), ('to', 'Tonga'), ('sb', 'Solomon Islands'), ('ki', 'Kiribati')]
    }

    # Randomly select 4 countries from each continent
    selected_countries = []
    for continent, countries in continents.items():
        selected_countries.extend(random.sample(countries, 4))

    # Fetch all the plans related to 'proxy_aggregator' service
    plans = SubscriptionItem.objects.filter(service_name='proxy_aggregator')
    
    return render(request, 'extras/proxy_aggregator.html', {
        'plans': plans, 
        'selected_countries': selected_countries,
        'more_countries': True  # Flag to indicate there are more countries
    })
