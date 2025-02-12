from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from tutorials.models.admin_models import Admin
from tutorials.models.admin_models import Notification

def is_admin(user):
    return user.role == 'Admin'

@user_passes_test(is_admin)
def admin_home_page(request):
    admins = Admin.objects.all()
    return render(request, 'admin_home_page.html', {'admins': admins})

def admin_job_listings(request):
    return render(request, 'admin_job_listings.html')

@user_passes_test(is_admin)
def admin_notifications(request):
    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')

    notifications.update(is_read=True)

    return render(request, 'admin_notifications.html', {
        'notifications': notifications,
        'unread_count': unread_count, 
    })

