from django.urls import path

from .views import (
    HomeView,
    LoginView,
    LogoutView,

    JobsListView,
    JobsView,
    JobsUpdateView,
    job_update,

    AddNewSkil,
    SkillsListView,
    UpdateSkill,

    LocationsListView,
    AddNewLocation,
    GetIso2Iso3,
    UpdateLocation,

    CompaniesListView,
    CompaniesUpdateView,
    CompaniesCreateView,

    search_companies,
    search_job_title,
    search_job_category,
    search_job_id,
    search_skills,
    search_state,
    search_city,
    search_country,

    DownloadLocations
)

urlpatterns = [

    path('', HomeView.as_view(), name='admin-home'),

    path('jobs/', JobsListView.as_view(), name='admin-jobs'),
    path('jobs/<pk>/', JobsView.as_view(), name='admin-job-detailed-view'),
    path('jobs/<pk>/update/', job_update, name='admin-jobs-update-view'),

    # skills
    path('skills/add/', AddNewSkil.as_view(), name='admin-add-new-skill'),
    path('skills/', SkillsListView.as_view(), name='admin-skills'),
    path('skills/update/', UpdateSkill.as_view(), name='admin-update-skill'),

    # locations
    path('locations/', LocationsListView.as_view(), name='admin-locations'),
    path('locations/add/', AddNewLocation.as_view(), name='admin-add-new-location'),
    path('locations/get-iso2-iso3/', GetIso2Iso3.as_view(), name='admin-get-iso2-iso3'),
    path('location/update/', UpdateLocation.as_view(), name='admin-update-location'),
    path('locations/download-csv', DownloadLocations.as_view(), name='download-locations-csv'),
    # Companies
    path('companies/', CompaniesListView.as_view(), name='admin-companies'),
    path('companies/update/<pk>/', CompaniesUpdateView.as_view(), name='admin-companies-update'),
    path('companies/add/', CompaniesCreateView.as_view(), name='admin-add-new-companies'),
    # autocomplete views
    path('search-company-name/', search_companies, name='admin-search-company-name'),
    path('search-job-title/', search_job_title, name='admin-search-job-title'),
    path('search-job-category/', search_job_category, name='admin-search-job-category'),
    path('search-job-jobid/', search_job_id, name='admin-search-job-jobid'),
    path('search-job-skills/', search_skills, name='admin-search-skills'),
    path('search-job-country/', search_country, name='admin-search-country'),
    path('search-job-city/', search_city, name='admin-search-city'),
    path('search-job-state/', search_state, name='admin-search-state'),
]
