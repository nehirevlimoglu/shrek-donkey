from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse  # Used for redirection
from django.contrib.auth.decorators import login_required
from tutorials.helpers import login_prohibited  # If used elsewhere
from tutorials.forms.forms import SignUpForm  # Form for signing up
from tutorials.forms.applicants_forms import ApplicantForm  # Applicant profile completion form
from tutorials.forms.employer_forms import EmployerProfileForm  # Employer profile completion form
from tutorials.models.applicants_models import Applicant  # Applicant model
from tutorials.models.employer_models import Employer  # Employer model


def log_in(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        print(f"Attempting login: {username} | {password}")  # ✅ Debugging step
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            print(f"User authenticated: {user.username} | Role: {user.role}")  # ✅ Debugging step
            login(request, user)

            # ✅ Redirect based on role
            if request.user.role == 'Admin':
                return redirect('admin_home_page')  
            elif request.user.role == 'Employer':
                return redirect('employer_home_page')  
            elif request.user.role == 'Applicant' or request.user.role == 'job_seeker':               
                return redirect('applicants-home-page')  
            

            raise Http404("Page not found")


        else:
            print("Authentication failed")  # ❌ This means the username/password is incorrect.
    
    return render(request, 'log_in.html')


def sign_up(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            # ✅ Ensure employer or applicant profile is created immediately
            if user.role == 'Employer':
                Employer.objects.create(user=user, username=user.username, email=user.email)  # ✅ Auto-create profile
                return redirect('employer_profile_setup')

            elif user.role == 'Applicant':
                Applicant.objects.create(user=user)  # ✅ Auto-create profile
                return redirect('applicant_profile_setup')

            return redirect('home')

    else:
        form = SignUpForm()

    return render(request, 'sign_up.html', {'form': form})


@login_required
def applicant_profile_setup(request):
    try:
        applicant = request.user.applicant
    except Applicant.DoesNotExist:
        applicant = None

    if request.method == 'POST':
        form = ApplicantForm(request.POST, request.FILES, user=request.user, instance=applicant)
        if form.is_valid():
            applicant = form.save(commit=False)
            applicant.user = request.user
            applicant.save()
            return redirect('applicants-home-page')  # ✅ Redirect AFTER profile completion

    else:
        form = ApplicantForm(user=request.user, instance=applicant)

    return render(request, 'applicant_profile_setup.html', {'form': form})

@login_required
def employer_profile_setup(request):
    try:
        employer = request.user.employer
    except Employer.DoesNotExist:
        employer = None

    if request.method == 'POST':
        form = EmployerProfileForm(request.POST, request.FILES, instance=employer)
        if form.is_valid():
            employer = form.save(commit=False)
            employer.user = request.user
            employer.save()
            return redirect('employer_home_page')  # ✅ Redirect AFTER profile completion

    else:
        form = EmployerProfileForm(instance=employer)

    return render(request, 'employer_profile_setup.html', {'form': form})



def log_out(request):

    print("User before logout:", request.user) 

    return redirect('log-in')  

    logout(request)  
    print("User after logout:", request.user)  
    return redirect('log-in')


def job_matching_view(request, job_id):
    """View to match candidates to a job based on extracted skills"""
    job = get_object_or_404(Job, id=job_id)
    matched_candidates = match_candidates_to_job(job.title, top_n=5)

    return render(request, "candidate_matches.html", {
        "job": job,
        "matched_candidates": matched_candidates
    })
    return redirect('log-in')
