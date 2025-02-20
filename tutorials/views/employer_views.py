from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from tutorials.models.employer_models import Employer, Job, Candidate, Interview
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

def view_employer_analytics(request):
    return render(request, 'employer_analytics.html')

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

def employer_job_listings(request):
    jobs = Job.objects.all()  
    return render(request, 'employer_job_listings.html', {'jobs': jobs})

def create_job_listings(request):
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            #job.employer = request.user.employer
            job.employer = None
            job.save()
            return redirect('employer_job_listings')  
    else:
        form = JobForm()

    return render(request, 'employer_create_job_listing.html', {'form': form})

def job_detail_view(request, pk):
    job = get_object_or_404(Job, pk=pk)
    return render(request, 'jobs/employer_job_detail.html', {'job': job})

def edit_job_view(request, pk):
    job = get_object_or_404(Job, pk=pk)

    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            return redirect('employer_job_detail', pk=job.pk)
    else:
        form = JobForm(instance=job)

    return render(request, 'jobs/edit_job.html', {'form': form, 'job': job})

    
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
            update_session_auth_hash(request, form.user)  # Prevents logout after password change
            messages.success(request, "Your password has been successfully changed.")  # Success message
            return redirect('employer_settings')  # Redirect to settings
        else:
            messages.error(request, "There was an issue with your password change. Please check and try again.")

    else:
        form = CustomPasswordChangeForm(user=request.user)
    
    return render(request, 'change_password.html', {'form': form})


@login_required
def employer_candidates(request):
    """ Ensure request.user is an Employer before querying """
    try:
        # Match Employer by username instead of user object
        employer = Employer.objects.get(username=request.user.username)  
        candidates = Candidate.objects.filter(job__employer=employer)
    except Employer.DoesNotExist:
        return HttpResponseForbidden("You are not an employer.")

    return render(request, 'employer_candidates.html', {'candidates': candidates})


@user_passes_test(is_employer)
@login_required
def employer_interviews(request):
    interviews = Interview.objects.filter(job__employer=request.user)
    return render(request, 'employer_interviews.html', {'interviews': interviews})
    
@user_passes_test(is_employer)
@login_required
def get_interviews(request):
    """ Fetch interview data for FullCalendar.js """
    interviews = Interview.objects.filter(job__employer=request.user)
    events = [
        {
            "title": f"{interview.candidate.user.first_name} - {interview.job.title}",
            "start": f"{interview.date}T{interview.time}",
        }
        for interview in interviews
    ]
    return JsonResponse(events, safe=False)