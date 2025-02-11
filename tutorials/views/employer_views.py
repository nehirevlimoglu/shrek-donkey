from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from tutorials.models.employer_models import Employer, Job
from tutorials.forms.forms import SignUpForm
from tutorials.forms.employer_forms import JobForm

def is_employer(user):
    return user.role == 'Employer'

@user_passes_test(is_employer)
def employer_home_page(request):
    employers = Employer.objects.all()
    return render(request, 'employers_home_page.html', {'employers': employers})

def view_listings(request):
    jobs = Job.objects.all()  
    return render(request, 'employer_job_listings.html', {'jobs': jobs})

def view_reports(request):
    return render(request, 'employer_reports.html')

def view_settings(request):
    return render(request, 'employer_settings.html')


def employer_sign_up(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            if user.role != 'Employer':  # Ensures only employers sign up here
                form.add_error(None, "Only employers can sign up.")
                return render(request, 'sign_up.html', {'form': form})
            
            user.save()
            login(request, user)  # Log in after sign-up
            return redirect('employer_home_page')  # Redirect to employer home page
    else:
        form = SignUpForm()

    return render(request, 'sign_up.html', {'form': form})

# Employer Login
def employer_login(request):
    if request.method == 'POST':
        form = LogInForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user and is_employer(user):  # Ensure only employers log in
                login(request, user)
                return redirect('employer_home_page')
            else:
                form.add_error(None, "Only employers can log in here.")
    else:
        form = LogInForm()
    return render(request, 'log_in.html', {'form': form})

def create_job_listing(request):
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.employer = request.user 
            job.save()
            return redirect('employer_job_listings')  
    else:
        form = JobForm()

    return render(request, 'employer_create_job_listing.html', {'form': form})

def job_detail_view(request, pk):
    # Attempt to retrieve the Job with the given primary key
    job = get_object_or_404(Job, pk=pk)
    # Render the 'job_detail.html' template, passing in the retrieved job
    return render(request, 'jobs/employer_job_detail.html', {'job': job})
