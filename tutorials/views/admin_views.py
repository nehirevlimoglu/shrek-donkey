from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from tutorials.models.admin_models import Admin

def is_admin(user):
    return user.role == 'Admin'

@user_passes_test(is_admin)
def admin_home_page(request):
    admins = Admin.objects.all()
    return render(request, 'admin_home_page.html', {'admins': admins})

def admin_job_listings(request):
    return render(request, 'admin_job_listings.html')