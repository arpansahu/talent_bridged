from django.shortcuts import render

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
