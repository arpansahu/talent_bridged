from django.contrib import admin
from .models import Skills

@admin.register(Skills)
class SkillsAdmin(admin.ModelAdmin):
    list_display = ('name', 'created', 'modified')
    search_fields = ('name',)
    ordering = ('name',)
