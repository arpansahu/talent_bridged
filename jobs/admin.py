from django.contrib import admin
from .models import Jobs, JobLocation, Keyword, UserKeyword, JobsStats
from locations.models import Locations

@admin.register(Keyword)
class KeywordAdmin(admin.ModelAdmin):
    list_display = ('word', 'created_at', 'frequency')
    search_fields = ('word',)
    ordering = ('-frequency',)  # Order by popularity

@admin.register(UserKeyword)
class UserKeywordAdmin(admin.ModelAdmin):
    list_display = ('word', 'search_count', 'jobs_found_count', 'last_searched')
    search_fields = ('word',)
    list_filter = ('last_searched',)
    actions = ['promote_to_keyword']

    def promote_to_keyword(self, request, queryset):
        for user_keyword in queryset:
            user_keyword.promote_to_keyword()
    promote_to_keyword.short_description = 'Promote selected keywords to main Keyword table'

@admin.register(Locations)
class LocationsAdmin(admin.ModelAdmin):
    list_display = ('city', 'state', 'country')
    search_fields = ('city', 'state', 'country')
    list_filter = ('country',)

@admin.register(JobLocation)
class JobLocationAdmin(admin.ModelAdmin):
    list_display = ('job', 'location', 'remote')
    search_fields = ('job__title', 'location__city', 'location__country')
    list_filter = ('remote',)
    autocomplete_fields = ['job', 'location']  # Enables autocomplete for job and location fields

@admin.register(Jobs)
class JobsAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'sub_category', 'company', 'date', 'available', 'remote', 'in_office')
    search_fields = ('title', 'post', 'company__name')
    list_filter = ('category', 'sub_category', 'available', 'remote', 'in_office', 'reviewed')
    filter_horizontal = ('required_skills',)  # Remove 'location' as it uses a through model
    ordering = ('-date',)

@admin.register(JobsStats)
class JobsStatsAdmin(admin.ModelAdmin):
    list_display = ('total_available', 'total_unavailable', 'date')
    readonly_fields = ('date',)  # Make date field read-only since it's auto-generated
