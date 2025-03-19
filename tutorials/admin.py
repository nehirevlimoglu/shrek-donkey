from django.contrib import admin
from .models.admin_models import Admin, Notification  # Import your models
from tutorials.models.employer_models import Job, JobTitle

@admin.register(Admin)
class AdminAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email')  # Adjust as per your model fields

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'recipient', 'message', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('recipient__username', 'message')

@admin.register(JobTitle)
class JobTitleAdmin(admin.ModelAdmin):
    list_display = ("title",)

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "company_name", "location", "job_type", "salary")
    list_filter = ("job_type", "location")
    search_fields = ("title__title", "company_name")

