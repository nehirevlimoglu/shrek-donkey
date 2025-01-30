from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from tutorials.models.applicants_models import Applicant
from tutorials.forms.applicants_forms import ApplicantForm

def applicants_home_page(request):
    return render(request, 'applicants_home_page.html')

def applicants_account(request):
    # Placeholder values for testing
    applicant_data = {
        'name': 'John',
        'surname': 'Doe',
        'degree': 'Bachelor of Computer Science',
        'salary_preferences': '$70,000 - $100,000/year',
        'job_preferences': 'Software Developer, Data Analyst',
        'location_preferences': 'Remote, New York, San Francisco',
        'cv': None,  # No CV uploaded yet
    }

    return render(request, 'applicants/account.html', {'applicant': applicant_data})

