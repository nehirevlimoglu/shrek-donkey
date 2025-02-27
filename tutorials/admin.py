from django.contrib import admin
from .models.admin_models import Admin, Notification  # Import your models

@admin.register(Admin)
class AdminAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email')  # Adjust as per your model fields

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'recipient', 'message', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('recipient__username', 'message')
