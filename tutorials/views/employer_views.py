from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from tutorials.models.employer_models import Employer
from tutorials.forms.forms import SignUpForm

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