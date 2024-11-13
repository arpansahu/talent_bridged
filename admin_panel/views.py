import csv
import datetime
import json
import codecs
from django.contrib.auth import authenticate, login, logout, REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
from django.db.models.functions import Lower
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import ListView, UpdateView, DetailView, CreateView, FormView
from django.views.generic.base import View, RedirectView
from django.contrib.auth import get_user_model
from companies.models import Company
from jobs.models import Jobs, JobsStats, Keyword, UserKeyword
from django.utils import timezone
from locations.models import Locations
from skills.models import Skills
from .forms import ModifyCompaniesForm
from django.db.models import Q
from django.db.models.functions import Length

from jobs.documents import JobDocument  # Import Elasticsearch document
from jobs.models import Jobs  # Import your Django model
from django.template.loader import render_to_string


now = timezone.now()
User = get_user_model()

# Set up logging
import logging
logger = logging.getLogger('django')




@method_decorator(login_required(redirect_field_name=''), name='dispatch')
class HomeView(View):
    def get(self, request):
        return render(request, 'home/index.html', context={'segment': 'home'})



@method_decorator(login_required(login_url='login'), name='dispatch')
class JobsListView(ListView):
    model = Jobs
    template_name = 'home/jobs/jobs.html'
    context_object_name = 'jobs_list'
    paginate_by = 10

    def get_queryset(self):
        self.title_keyword = ""
        self.location = ""
        self.category = ""
        self.sub_category = ""
        self.skills = ""
        self.companies = ""
        self.date_posted = ""
        self.remote = ""
        self.in_office = ""

        queryset = Jobs.objects.all().filter(available=True).prefetch_related('company', 'location', 'required_skills').order_by('id')
        request = self.request.GET
        
        # Title and post_text keyword filter
        title_keyword = request.get("title_keyword")

        if title_keyword:
            self.title_keyword = title_keyword
            title_queryset = queryset.filter(title__icontains=title_keyword)

            # Use Elasticsearch for full-text search on `post_text`, retrieving only the IDs
            es_results = JobDocument.search().query("match", post_text=title_keyword).source(False)
            es_job_ids = [hit.meta.id for hit in es_results.execute()]

            # Combine both PostgreSQL and Elasticsearch results
            queryset = queryset.filter(
                Q(id__in=es_job_ids) | Q(id__in=title_queryset.values_list('id', flat=True))
            )

        # Location filter
        location = request.get("location")

        if location:
            self.location = location
            # Split the location string into parts
            location_parts = [part.strip() for part in location.split(',')]
            city, state, country = None, None, None

            if len(location_parts) == 3:
                # When 3 parts are present, assume it's city, state, and country
                city, state, country = location_parts
            elif len(location_parts) == 1:
                # Treat the single part as either a city or a country
                potential_city_or_country = location_parts[0]

            # Apply filtering for each part that is available
            if city:
                queryset = queryset.filter(location__city__iexact=city)
            if state:
                queryset = queryset.filter(location__state__iexact=state)
            if country:
                queryset = queryset.filter(location__country__iexact=country)
            elif potential_city_or_country:
                # Filter for either city or country when there's a single part
                queryset = queryset.filter(
                    Q(location__city__iexact=potential_city_or_country) |
                    Q(location__country__iexact=potential_city_or_country)
                )

        # Category filter (multiple categories allowed)
        category = request.get("category")
        if category:
            # Split the comma-separated string into a list if needed
            category_list = category.split(",")
            self.category = category
            queryset = queryset.filter(category__in=category_list)


        # Sub-category filter (multiple sub-categories allowed)
        sub_category = request.get("sub_category")
        if sub_category:
            # Split the comma-separated string into a list if needed
            sub_category_list = sub_category.split(",")
            self.sub_category = sub_category
            queryset = queryset.filter(sub_category__in=sub_category_list)


        # Skills filter (multiple skills allowed)
        skills = request.get("skills")
        if skills:

            skills_list = skills.split(",")
            self.skills = skills

            queryset = queryset.filter(required_skills__name__in=skills)


        # Company filter (multiple companies allowed)
        companies = request.get("companies")
        if companies:
            # Split the comma-separated string into a list if needed
            companies_list = companies.split(",")
            self.companies = companies
            queryset = queryset.filter(company__name__in=companies_list)

        
        # Date Posted filter
        date_posted = request.get("date")
        if date_posted:
            today = timezone.now()
            self.date_posted = date_posted
            if date_posted == "last_24_hours":
                queryset = queryset.filter(date__gte=today - datetime.timedelta(days=1))
            elif date_posted == "last_7_days":
                queryset = queryset.filter(date__gte=today - datetime.timedelta(days=7))
            elif date_posted == "last_30_days":
                queryset = queryset.filter(date__gte=today - datetime.timedelta(days=30))
        
        # Work type filter
        if request.get("remote") == "true":
            self.remote = True
            queryset = queryset.filter(remote=True)
        if request.get("in_office") == "true":
            self.in_office = True
            queryset = queryset.filter(in_office=True)
        

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['segment'] = 'jobs'

        today = timezone.now()
        today_min = timezone.make_aware(datetime.datetime.combine(today.date(), datetime.time.min))
        today_max = timezone.make_aware(datetime.datetime.combine(today.date(), datetime.time.max))

        # Jobs stats for today
        new_jobs = Jobs.objects.filter(date__range=(today_min, today_max)).count()
        total_jobs = Jobs.objects.filter(available=True).count()
        total_unavailable_jobs = Jobs.objects.filter(available=False).count()
        non_reviewed_jobs = Jobs.objects.filter(available=True, reviewed=False).count()

        # Percentage of new jobs
        total_jobs_list = context.get('jobs_list', [])
        new_jobs_perc = (new_jobs / len(total_jobs_list)) * 100 if total_jobs_list else 0

        # Setting the context for today’s job stats
        context.update({
            'new_jobs': new_jobs,
            'new_jobs_perc': new_jobs_perc,
            'total_jobs': total_jobs,
            'total_unavailable_jobs': total_unavailable_jobs,
            'total_non_reviewed': non_reviewed_jobs,
        })

        # Yesterday's job stats
        yesterday_min = today_min - datetime.timedelta(days=1)
        yesterday_max = today_max - datetime.timedelta(days=1)

        yesterday_jobs = JobsStats.objects.filter(date__range=(yesterday_min, yesterday_max)).first()
        if yesterday_jobs and yesterday_jobs.total_available:
            context['total_jobs_change'] = ((total_jobs - yesterday_jobs.total_available) / yesterday_jobs.total_available) * 100
            context['total_jobs_change_positive'] = context['total_jobs_change'] > 0
        else:
            context['total_jobs_change'] = 0
            context['total_jobs_change_positive'] = False

        # Yesterday's unavailable job stats
        if yesterday_jobs and yesterday_jobs.total_unavailable:
            context['total_unavailable_jobs_change'] = ((total_unavailable_jobs - yesterday_jobs.total_unavailable) / yesterday_jobs.total_unavailable) * 100
        else:
            context['total_unavailable_jobs_change'] = 0

        # Selected filters data from instance variables
        context.update({
            'selected_title_keyword': self.title_keyword,
            'selected_location': self.location,
            'selected_date_posted': self.date_posted,
            'selected_remote': self.remote,
            'selected_in_office': self.in_office,
            'selected_category': self.category,
            'selected_sub_category': self.sub_category,
            'selected_skills': self.skills,
            'selected_companies': self.companies
        })

        return context

    def render_to_response(self, context, **response_kwargs):
        # Check if the request is an AJAX call by inspecting headers
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            jobs_html = render_to_string('home/jobs/job_list_partial.html', context)
            return JsonResponse({
                'jobs_html': jobs_html,
                'has_next': context['page_obj'].has_next(),
                'next_page_number': context['page_obj'].next_page_number() if context['page_obj'].has_next() else None
            })
        return super().render_to_response(context, **response_kwargs)

@method_decorator(login_required(login_url='login'), name='dispatch')
class JobsView(DetailView):
    model = Jobs
    template_name = 'home/jobs/jobs-detailed.html'
    context_object_name = 'job'
    pk_url_kwarg = 'id'  # Specify that 'id' should be used as the primary key in the URL


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['segment'] = 'jobs'
        return context


class JobsUpdateView(UpdateView):
    model = Jobs
    fields = ['required_skills', 'required_experience']
    template_name = 'home/jobs/jobs-update.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['segment'] = 'jobs'

        all_skills = Skills.objects.filter(jobs=self.object)
        skill_string = ', '.join(skill.name for skill in all_skills)
        context['skills_string'] = skill_string
        return context

    def get_success_url(self):
        return reverse('jobs/' + str(self.object.pk) + '/')


@login_required()
def job_update(request, pk):
    job_obj = get_object_or_404(Jobs, id=pk)

    context = {'segment': 'jobs', 'job': job_obj}

    if request.POST:
        required_skills = (request.POST['all_skills']).split(', ')
        required_experience = request.POST['required_years']
        reviewed = request.POST['reviewed']

        job_obj.required_skills.clear()

        for skill in required_skills:
            skill_obj = Skills.objects.get(name=skill)
            if skill_obj:
                job_obj.required_skills.add(skill_obj)
        if required_experience:
            job_obj.required_experience = int(required_experience)
        if reviewed == 'unreviewed':
            job_obj.reviewed = False
        else:
            job_obj.reviewed = True

        job_obj.save()

    all_skills = job_obj.required_skills.all()
    skill_string = ', '.join(skill.name for skill in all_skills)
    context['skills_string'] = skill_string
    context['reviewed'] = job_obj.reviewed
    return render(request, "home/jobs/jobs-update.html", context)


# views for javascript functions
@login_required()
def autocomplete_title_keywords(request):
    query = request.GET.get('q', '').strip()
    logger.info(f"Received autocomplete request with query: '{query}'")

    suggestions = set()

    if query:
        # Fetch job titles matching the query
        job_titles = Jobs.objects.filter(title__icontains=query).values_list('title', flat=True)[:5]
        suggestions.update(job_titles)
        logger.info(f"Job titles found: {list(job_titles)}")
        
        # Fetch keywords matching the query
        keywords = Keyword.objects.filter(word__icontains=query).values_list('word', flat=True)[:5]
        suggestions.update(keywords)
        logger.info(f"Keywords found: {list(keywords)}")
        
        # Fetch user keywords and update counts
        user_keywords = UserKeyword.objects.filter(word__icontains=query).values('word', 'search_count', 'jobs_found_count')[:10]
        logger.info(f"User keywords found: {list(user_keywords)}")

        for user_keyword in user_keywords:
            word = user_keyword['word']
            search_count = user_keyword['search_count']
            jobs_found_count = user_keyword['jobs_found_count']

            # Add word to suggestions and update UserKeyword counts
            suggestions.add(word)
            UserKeyword.objects.filter(word=word).update(search_count=search_count + 1, last_searched=timezone.now())

            # Promote UserKeyword to Keyword if criteria are met
            if search_count + 1 >= 10 and jobs_found_count >= 10:
                Keyword.objects.get_or_create(word=word)
                UserKeyword.objects.filter(word=word).delete()

    # Prepare response and log it
    suggestions_list = sorted(list(suggestions))  # Sorting for consistency
    logger.info(f"Final suggestions for query '{query}': {suggestions_list}")

    return JsonResponse({
        'status': 200,
        'data': suggestions_list
    })

def autocomplete_locations(request):
    query = request.GET.get('q', '').strip()
    logger.info(f"Received query for autocomplete: '{query}'")

    location_suggestions = set()  # Use a set to avoid duplicates

    if query:
        # Fetch country-only matches
        country_matches = Locations.objects.filter(country__icontains=query).values_list('country', flat=True).distinct()[:10]
        location_suggestions.update(country_matches)
        logger.info(f"Country matches found: {list(country_matches)}")

        # Fetch city, state, and country combinations matching the query
        location_matches = Locations.objects.filter(
            Q(city__icontains=query) | Q(state__icontains=query) | Q(country__icontains=query)
        ).values('city', 'state', 'country').distinct()[:10]

        # Format results as "City, State, Country" and add to suggestions
        formatted_locations = [
            ", ".join(filter(None, [location['city'], location['state'], location['country']]))
            for location in location_matches
        ]
        location_suggestions.update(formatted_locations)
        logger.info(f"Formatted location matches found: {formatted_locations}")

    # Convert set to list, sort for consistency, and log
    location_suggestions = sorted(list(location_suggestions))
    logger.info("======================================")
    logger.info(f"Final response data: {location_suggestions}")

    return JsonResponse({
        'status': 200,
        'data': location_suggestions
    })

@login_required()
def autocomplete_skills(request):
    query = request.GET.get('q', '').strip()
    logger.info(f"Received query for autocomplete: '{query}'")

    skill_suggestions = []

    if query:
        # Filter based on matching query with skill name, then annotate with length and order by it
        skills = (
            Skills.objects
            .filter(name__icontains=query)
            .annotate(name_length=Length('name'))
            .order_by('name_length')  # Sort by name length, shortest first
            .values('name')
            .distinct()[:10]
        )

        # Log query results for debugging
        logger.info(f"Database query returned: {list(skills)}")

        # Extract the skill names into a list
        skill_suggestions = [skill.get('name') for skill in skills]

    # Log the final response data to confirm it before returning
    logger.info("======================================")
    logger.info(f"Final response data: {skill_suggestions}")

    # Construct the response payload
    payload = {
        'status': 200,
        'data': skill_suggestions
    }

    return JsonResponse(payload)

@login_required()
def autocomplete_companies(request):
    query = request.GET.get('q', '').strip()
    logger.info(f"Received query for company autocomplete: '{query}'")

    company_suggestions = []

    if query:
        # Filter companies based on query, annotate with length, and order by it
        companies = (
            Company.objects
            .filter(name__icontains=query)
            .annotate(name_length=Length('name'))
            .order_by('name_length')  # Sort by name length, shortest first
            .values('name')
            .distinct()[:10]
        )

        # Log query results for debugging
        logger.info(f"Database query returned: {list(companies)}")

        # Extract the company names into a list
        company_suggestions = [company.get('name') for company in companies]

    # Log the final response data to confirm it before returning
    logger.info("======================================")
    logger.info(f"Final response data: {company_suggestions}")

    # Construct the response payload
    payload = {
        'status': 200,
        'data': company_suggestions
    }

    return JsonResponse(payload)

@login_required
def autocomplete_category(request):
    query = request.GET.get('q', '').strip()
    logger.info(f"Received autocomplete request for category with query: '{query}'")
    
    category_suggestions = []

    if query:
        # Fetch categories, annotate with length, and order by length (shorter first)
        categories = (
            Jobs.objects
            .filter(category__icontains=query)
            .values_list('category', flat=True)
            .annotate(category_length=Length('category'))
            .order_by('category_length')
            .distinct()[:10]
        )

        # Log categories found
        logger.info(f"Categories found for query '{query}': {list(categories)}")
        category_suggestions = list(categories)

    # Construct the response payload
    payload = {
        'status': 200,
        'data': category_suggestions
    }

    # Log the final response
    logger.info(f"Final category suggestions: {category_suggestions}")
    return JsonResponse(payload)


@login_required
def autocomplete_sub_category(request):
    query = request.GET.get('q', '').strip()
    logger.info(f"Received autocomplete request for sub-category with query: '{query}'")
    
    sub_category_suggestions = []

    if query:
        # Fetch sub-categories, annotate with length, and order by length (shorter first)
        sub_categories = (
            Jobs.objects
            .filter(sub_category__icontains=query)
            .values_list('sub_category', flat=True)
            .annotate(sub_category_length=Length('sub_category'))
            .order_by('sub_category_length')
            .distinct()[:10]
        )

        # Log sub-categories found
        logger.info(f"Sub-categories found for query '{query}': {list(sub_categories)}")
        sub_category_suggestions = list(sub_categories)

    # Construct the response payload
    payload = {
        'status': 200,
        'data': sub_category_suggestions
    }

    # Log the final response
    logger.info(f"Final sub-category suggestions: {sub_category_suggestions}")
    return JsonResponse(payload)


@login_required()
def search_companies(request):
    company = request.GET.get('company')
    payload = []
    if company:
        companies_objs = Company.objects.filter(name__icontains=company)

        for objs in companies_objs:
            payload.append(objs.name)

    return JsonResponse({'status': 200, 'data': payload})


@login_required()
def search_job_title(request):
    title = request.GET.get('title')
    payload = []
    if title:
        job_objs = Jobs.objects.filter(title__icontains=title)

        for objs in job_objs:
            payload.append(objs.title)
    payload = list(set(payload))
    return JsonResponse({'status': 200, 'data': payload})


@login_required()
def search_job_category(request):
    category = request.GET.get('category')
    payload = []
    if category:
        job_objs = Jobs.objects.filter(category__icontains=category)

        for objs in job_objs:
            payload.append(objs.category)
    payload = list(set(payload))
    return JsonResponse({'status': 200, 'data': payload})


@login_required()
def search_job_id(request):
    job_id = request.GET.get('jobid')
    payload = []
    if job_id:
        job_objs = Jobs.objects.filter(job_id__icontains=job_id)

        for objs in job_objs:
            payload.append(objs.job_id)
    payload = list(set(payload))
    return JsonResponse({'status': 200, 'data': payload})




@login_required()
def search_country(request):
    name = request.GET.get('country')
    payload = []
    if name:
        locations_obj = Locations.objects.filter(country__icontains=name)

        for objs in locations_obj:
            payload.append(objs.country)
    payload = list(set(payload))
    return JsonResponse({'status': 200, 'data': payload})


def search_city(request):
    name = request.GET.get('city')
    payload = []
    if name:
        locations_obj = Locations.objects.filter(city__icontains=name)

        for objs in locations_obj:
            payload.append(objs.city)
    payload = list(set(payload))
    return JsonResponse({'status': 200, 'data': payload})


def search_state(request):
    name = request.GET.get('state')
    payload = []
    if name:
        locations_obj = Locations.objects.filter(state__icontains=name)

        for objs in locations_obj:
            payload.append(objs.state)
    payload = list(set(payload))
    return JsonResponse({'status': 200, 'data': payload})


@method_decorator(login_required(login_url='login'), name='dispatch')
class SkillsListView(ListView):
    model = Skills
    template_name = 'home/jobs/skills/skills.html'
    context_object_name = 'skills_list'
    paginate_by = 10
    queryset = Skills.objects.all().order_by('id')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all_skills_count'] = Skills.objects.all().count()
        context['segment'] = 'jobs'
        return context


@method_decorator(login_required(login_url='login'), name='dispatch')
class AddNewSkill(View):

    def post(self, request, *args, **kwargs):
        skill = request.POST.get('skill')
        message = ''
        if skill:
            obj, created = Skills.objects.get_or_create(name=skill)
            if created:
                message = f"New Skill {obj.name} Added successfully"
            else:
                message = f"Skill {obj.name} already exists"
            return JsonResponse({'status': 200, 'message': message})
        else:
            message = "No Skill Received"
            return JsonResponse({'status': 400, 'message': message})


@method_decorator(login_required(login_url='login'), name='dispatch')
class UpdateSkill(View):
    def post(self, request, *args, **kwargs):
        skill = request.POST.get('skill')
        id = request.POST.get('id')
        message = ''
        if skill and id:
            obj = get_object_or_404(Skills, id=id)
            if obj.name != skill:
                obj.name = skill
                obj.save()
                message = f"Skill {obj.name} Updated successfully"
            else:
                message = f"Skill {obj.name} Have No Changes"
            return JsonResponse({'status': 200, 'message': message})
        else:
            message = "No Skill Received"
            return JsonResponse({'status': 400, 'message': message})


@method_decorator(login_required(login_url='login'), name='dispatch')
class LocationsListView(ListView):
    model = Locations
    template_name = 'home/jobs/locations/locations.html'
    context_object_name = 'locations_list'
    paginate_by = 10
    queryset = Locations.objects.all().order_by('id')

    def get_queryset(self):
        queryset = self.queryset
        if self.request.GET.get("country"):
            queryset = queryset.filter(country=self.request.GET.get("country"))

        if self.request.GET.get("city"):
            queryset = queryset.filter(city=self.request.GET.get("city"))
        
        if self.request.GET.get("state"):
            queryset = queryset.filter(state=self.request.GET.get("state"))

        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all_locations_count'] = Locations.objects.all().count()
        context['segment'] = 'jobs'

        return context


@method_decorator(login_required(login_url='login'), name='dispatch')
class GetIso2Iso3(View):
    def get(self, request, *args, **kwargs):
        country = self.request.GET.get('country')
        message = ''
        if country:
            obj = Locations.objects.filter(country=country).first()
            if obj:
                message = f'Iso2: {obj.country_code_iso2} and Iso3: {obj.country_code_iso3}'
                iso2 = obj.country_code_iso2
                iso3 = obj.country_code_iso3
            else:
                message = f"No Records found with country : {country}"
                iso2 = ''
                iso3 = ''
            return JsonResponse({'status': 200, 'message': message, 'iso2': iso2, 'iso3': iso3})
        else:
            message = "No Country Received"
            return JsonResponse({'status': 400, 'message': message})


@method_decorator(login_required(login_url='login'), name='dispatch')
class AddNewLocation(View):
    def post(self, request, *args, **kwargs):
        city = self.request.POST.get('city')
        country = self.request.POST.get('country')
        iso2 = self.request.POST.get('iso2')
        iso3 = self.request.POST.get('iso3')
        state = self.request.POST.get('state')

        if city and country and iso2 and iso3:
            obj, created = Locations.objects.get_or_create(city=city, country=country, country_code_iso3=iso3,
                                                  country_code_iso2=iso2, state=state)
            if created:
                message = f"New Location with City: {obj.city} Country: {obj.country} Iso2: {obj.country_code_iso2} Iso3: {obj.country_code_iso3} State: {obj.state} Added successfully"
            else:
                message = f"Location with City: {obj.city} Country: {obj.country} Iso2: {obj.country_code_iso2} Iso3: {obj.country_code_iso3} State: {obj.state} already exists"
            return JsonResponse({'status': 200, 'message': message})
        else:
            message = "Sufficient Information Not Received"
            return JsonResponse({'status': 400, 'message': message})


@method_decorator(login_required(login_url='login'), name='dispatch')
class UpdateLocation(View):
    def post(self, request, *args, **kwargs):
        city = self.request.POST.get('city')
        country = self.request.POST.get('country')
        iso2 = self.request.POST.get('iso2')
        iso3 = self.request.POST.get('iso3')
        id = self.request.POST.get('id')
        state = self.request.POST.get('state')

        message = ''

        if city and country and iso2 and iso3 and id and state:
            obj = get_object_or_404(Locations, id=id)
            if obj.city != city:
                message += f"Location with City: {obj.city} Updated to {city} successfully\n"
                obj.city = city
                obj.save()

            if obj.country != country:
                message += f"Location with Country: {obj.country} Updated to {country} successfully\n"
                obj.country = country
                obj.save()

            if obj.country_code_iso2 != iso2:
                message += f"Location with Iso2: {obj.country_code_iso2} Updated to {iso2} successfully\n"
                obj.country_code_iso2 = iso2
                obj.save()

            if obj.country_code_iso3 != iso3:
                message += f"Location with Country: {obj.country_code_iso3} Updated to {iso3} successfully\n"
                obj.country_code_iso3 = iso3
                obj.save()

            if obj.state != state:
                message += f"Location with State: {obj.state} Updated to {state} successfully\n"
                obj.state = state
                obj.save()
            
            if not message:
                message = "Location Have No Changes"
            
            return JsonResponse({'status': 200, 'message': message})
        else:
            message = "Sufficient Information Not Received"
            return JsonResponse({'status': 400, 'message': message})


@method_decorator(login_required(login_url='login'), name='dispatch')
class CompaniesListView(ListView):
    model = Locations
    template_name = 'home/jobs/companies/companies.html'
    context_object_name = 'companies_list'
    paginate_by = 10
    queryset = Company.objects.all().order_by('id')

    def get_queryset(self):
        queryset = self.queryset
        if self.request.GET.get("company-name"):
            queryset = queryset.filter(name=self.request.GET.get("company-name"))

        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all_companies_count'] = Company.objects.all().count()
        context['segment'] = 'jobs'

        if self.request.GET.get("company-name"):
            context['companyname'] = self.request.GET.get("company-name")

        return context


@method_decorator(login_required(login_url='login'), name='dispatch')
class CompaniesUpdateView(UpdateView):
    template_name = 'home/jobs/companies/companies-update.html'
    model = Company
    form_class = ModifyCompaniesForm
    success_url = '/companies/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['segment'] = 'jobs'
        return context


@method_decorator(login_required(login_url='login'), name='dispatch')
class CompaniesCreateView(CreateView):
    template_name = 'home/jobs/companies/companies-create.html'
    model = Company
    form_class = ModifyCompaniesForm
    success_url = '/companies/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['segment'] = 'jobs'
        return context


@method_decorator(login_required(login_url='login'), name='dispatch')
class DownloadLocations(View):
    # Create the HttpResponse object with the appropriate CSV header.
    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=locations.csv'
        # Create the CSV writer using the HttpResponse as the "file"
        writer = csv.writer(response)
        writer.writerow(['ID', 'City', 'Country', 'ISO2', 'ISO3', 'State'])
        all_locations = Locations.objects.filter().order_by('id')
        for locations in all_locations:
            writer.writerow([locations.id, locations.city, locations.country, locations.country_code_iso2,
                             locations.country_code_iso3, locations.state])

        return response
