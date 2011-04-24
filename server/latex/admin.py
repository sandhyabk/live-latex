from latex.models import *
from django.contrib import admin

class ProjectAdmin(admin.ModelAdmin):
	fields = ['author', 'short_name', 'long_name', 'description']
	
admin.site.register(Project, ProjectAdmin)