from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from tutorials.models.employer_models import Employer, Job
from tutorials.forms.forms import SignUpForm, LogInForm
from tutorials.forms.employer_forms import JobForm, CustomPasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash

def is_employer(user):
    return hasattr(user, 'role') and user.role == 'Employer'

@user_passes_test(is_employer)
def employer_home_page(request):
    employers = Employer.objects.all()
    return render(request, 'employers_home_page.html', {'employers': employers})

def view_reports(request):
    return render(request, 'employer_reports.html')

@login_required
def employer_settings(request):
    return render(request, 'employer_settings.html')

def employer_sign_up(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            if user.role != 'Employer':
                form.add_error(None, "Only employers can sign up.")
                return render(request, 'sign_up.html', {'form': form})
            user.save()
            login(request, user)
            return redirect('employer_home_page')
    else:
        form = SignUpForm()
    return render(request, 'sign_up.html', {'form': form})

def create_job_listings(request):
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

def employer_login(request):
    if request.method == 'POST':
        form = LogInForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user and is_employer(user):
                login(request, user)
                return redirect('employer_home_page')
            else:
                form.add_error(None, "Only employers can log in here.")
    else:
        form = LogInForm()
    return render(request, 'log_in.html', {'form': form})

@login_required
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)  # Prevent logout after password change
            return redirect('password_change_done')  # Redirect to a success page
    else:
        form = CustomPasswordChangeForm(user=request.user)
    
    return render(request, 'change_password.html', {'form': form})

