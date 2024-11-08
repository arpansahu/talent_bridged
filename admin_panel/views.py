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
from jobs.models import Jobs, JobsStats, Keyword
from django.utils import timezone
from locations.models import Locations
from skills.models import Skills
from .forms import ModifyCompaniesForm


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
        queryset = Jobs.objects.all().prefetch_related('company', 'location', 'required_skills').order_by('id')
        if self.request.GET.get("reviewed") == 'unreviewed':
            queryset = queryset.filter(reviewed=False)

        elif self.request.GET.get("reviewed") == 'reviewed':
            queryset = queryset.filter(reviewed=True)

        if self.request.GET.get("available") == 'available':
            queryset = queryset.filter(available=True)

        elif self.request.GET.get("available") == 'unavailable':
            queryset = queryset.filter(available=False)

        if self.request.GET.get("skill"):
            skill = Skills.objects.get(name=self.request.GET.get("skill"))
            queryset = queryset.filter(required_skills=skill.id)

        if self.request.GET.get("date-range"):
            obj = self.request.GET.get("date-range").split(' to ')
            if len(obj) == 2:
                from_date = timezone.make_aware(datetime.datetime.strptime(obj[0], '%Y-%m-%d'))
                to_date = timezone.make_aware(datetime.datetime.strptime(obj[1], '%Y-%m-%d')) + datetime.timedelta(days=1)
            if len(obj) == 1:
                from_date = timezone.make_aware(datetime.datetime.strptime(obj[0], '%Y-%m-%d'))
                to_date = timezone.make_aware(datetime.datetime.strptime(obj[0], '%Y-%m-%d')) + datetime.timedelta(days=1)

            queryset = queryset.filter(date__range=[from_date, to_date])

        if self.request.GET.get("company-name"):
            queryset = queryset.filter(company_id__name=self.request.GET.get("company-name"))

        if self.request.GET.get("job-title"):
            queryset = queryset.filter(title=self.request.GET.get("job-title"))

        if self.request.GET.get("job-category"):
            queryset = queryset.filter(category=self.request.GET.get("job-category"))

        if self.request.GET.get("job-country"):
            queryset = queryset.filter(location__country=self.request.GET.get("job-country"))

        if self.request.GET.get("job-city"):
            queryset = queryset.filter(location__city=self.request.GET.get("job-city"))

        if self.request.GET.get("job-state"):
            queryset = queryset.filter(location__state=self.request.GET.get("job-state"))

        if self.request.GET.get("job-job-id"):
            queryset = queryset.filter(job_id=self.request.GET.get("job-job-id"))

        return queryset

    def get_context_data(self, **kwargs):
        logger.info("ARpansahurocks")
        context = super().get_context_data(**kwargs)
        context['segment'] = 'jobs'
        company_list = Company.objects.all()
        context['company_list'] = company_list
        
        today_min = timezone.make_aware(datetime.datetime.combine(datetime.date.today(), datetime.time.min))
        today_max = timezone.make_aware(datetime.datetime.combine(datetime.date.today(), datetime.time.max))
        new_jobs = Jobs.objects.filter(date__range=(today_min, today_max)).count()
        
        try:
            new_jobs_perc = (new_jobs / context['jobs_list'].count()) * 100
        except ZeroDivisionError:
            new_jobs_perc = 0
        
        context['new_jobs'] = new_jobs
        context['new_jobs_perc'] = new_jobs_perc
        context['total_jobs'] = Jobs.objects.filter(available=True).count()
        
        yesterday_min = timezone.make_aware(datetime.datetime.combine(datetime.date.today() - datetime.timedelta(days=1), datetime.time.min))
        yesterday_max = timezone.make_aware(datetime.datetime.combine(datetime.date.today() - datetime.timedelta(days=1), datetime.time.max))
        total_yesterday_jobs = JobsStats.objects.filter(date__range=(yesterday_min, yesterday_max)).first()

        try:
            if total_yesterday_jobs and total_yesterday_jobs.total_available:
                context['total_jobs_change'] = ((context['total_jobs'] - total_yesterday_jobs.total_available) / total_yesterday_jobs.total_available) * 100
                context['total_jobs_change_positive'] = context['total_jobs_change'] > 0
            else:
                context['total_jobs_change'] = 0
        except:
            context['total_jobs_change'] = 0

        context['total_unavailable_jobs'] = Jobs.objects.filter(available=False).count()
        total_yesterday_unavailable_jobs = JobsStats.objects.filter(date__range=(yesterday_min, yesterday_max)).first()
        
        try:
            if total_yesterday_unavailable_jobs and total_yesterday_unavailable_jobs.total_unavailable:
                context['total_unavailable_jobs_change'] = ((context['total_unavailable_jobs'] - total_yesterday_unavailable_jobs.total_unavailable) / total_yesterday_unavailable_jobs.total_unavailable) * 100
            else:
                context['total_unavailable_jobs_change'] = 0
        except:
            context['total_unavailable_jobs_change'] = 0
        
        total_non_reviewed = Jobs.objects.filter(available=True, reviewed=False).count()
        context['total_non_reviewed'] = total_non_reviewed

        return context


@method_decorator(login_required(login_url='login'), name='dispatch')
class JobsView(DetailView):
    model = Jobs
    template_name = 'home/jobs/jobs-detailed.html'
    context_object_name = 'job'

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
    suggestions = []

    if query:
        # Get matching job titles
        job_titles = Jobs.objects.filter(title__icontains=query).values_list('title', flat=True)[:10]
        
        # Get matching keywords
        keywords = Keyword.objects.filter(name__icontains=query).values_list('name', flat=True)[:10]
        
        # Combine job titles and keywords into a single list
        suggestions = list(job_titles) + list(keywords)

    # Remove duplicates and send as JSON response
    suggestions = list(set(suggestions))  # Remove duplicates
    return JsonResponse(suggestions, safe=False)



def autocomplete_locations(request):
    from django.db.models import Q  # Add this import at the top
    query = request.GET.get('q', '').strip()
    logger.info(f"Received query for autocomplete: '{query}'")

    location_suggestions = []

    if query:
        # Filter based on matching query with city, state, or country
        locations = Locations.objects.filter(
            Q(city__icontains=query) | Q(state__icontains=query) | Q(country__icontains=query)
        ).values('city', 'state', 'country').distinct()[:10]

        # Log query results for debugging
        logger.info(f"Database query returned: {list(locations)}")

        # Construct a readable location format
        location_suggestions = [
            f"{location['city']}, {location['state']}, {location['country']}".strip(', ')
            for location in locations
        ]

    # Log the final response data to confirm it before returning
    logger.info(f"======================================")
    logger.info(f"Final response data: {location_suggestions}")
    return JsonResponse(location_suggestions, safe=False)

@login_required()
def autocomplete_skills(request):
    name = request.GET.get('name')
    payload = []
    if name:
        skill_objs = Skills.objects.filter(name__icontains=name)

        for objs in skill_objs:
            payload.append(objs.name)
    payload = list(set(payload))
    logger.info(f"payload is {payload}")
    return JsonResponse({'status': 200, 'data': payload})


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
