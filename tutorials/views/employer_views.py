from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from tutorials.models.employer_models import Employer

def is_employer(user):
    return user.role == 'Employer'

@user_passes_test(is_employer)
def employer_home_page(request):
    employers = Employer.objects.all()
    return render(request, 'employers_home_page.html', {'employers': employers})

def view_listings(request):
    return render(request, 'employer_job_listings.html')

def view_reports(request):
    return render(request, 'employer_reports.html')

def view_settings(request):
    return render(request, 'employer_settings.html')