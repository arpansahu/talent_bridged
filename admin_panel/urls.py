from django.urls import path

from .views import (
    HomeView,

    JobsListView,
    JobsView,
    JobsUpdateView,
    job_update,

    AddNewSkill,
    SkillsListView,
    UpdateSkill,

    LocationsListView,
    AddNewLocation,
    GetIso2Iso3,
    UpdateLocation,

    CompaniesListView,
    CompaniesUpdateView,
    CompaniesCreateView,



    autocomplete_skills,
    autocomplete_locations,
    autocomplete_title_keywords,
    search_companies,
    search_job_title,
    search_job_category,
    search_job_id,

    search_state,
    search_city,
    search_country,

    DownloadLocations
)

urlpatterns = [

    path('admin/', HomeView.as_view(), name='admin-home'),

    path('', JobsListView.as_view(), name='jobs'),
    path('jobs/<uuid:id>/', JobsView.as_view(), name='job_detailed_view'),
    path('jobs/<uuid:id>/update/', job_update, name='job_update_view'),


    # skills
    path('skills/add/', AddNewSkill.as_view(), name='admin-add-new-skill'),
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

    path('autocomplete-skills/', autocomplete_skills, name='autocomplete_skills'),
    path('autocomplete-locations/', autocomplete_locations, name='autocomplete_locations'),
    path('autocomplete-title-keyword/', autocomplete_title_keywords, name='autocomplete_title_keywords'),
]
