from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import user_passes_test
from tutorials.models.employer_models import Employer, Job, Candidate, Interview
from tutorials.forms.forms import SignUpForm, LogInForm
from schedule.models import Calendar, Event
from tutorials.forms.employer_forms import JobForm, EmployerProfileForm, CustomPasswordChangeForm, InterviewForm
from tutorials.forms.forms import CustomPasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.http import JsonResponse, HttpResponseForbidden
from django.core.exceptions import PermissionDenied


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

@login_required
def employer_job_listings(request):
    """ Display only the jobs posted by the logged-in employer """
    
    # Get the employer linked to the logged-in user
    try:
        employer = Employer.objects.get(username=request.user.username)
        jobs = Job.objects.filter(employer=employer)  # ✅ Get jobs posted by this employer
    except Employer.DoesNotExist:
        jobs = []  # ✅ If employer does not exist, show no jobs

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
    try:
        # Match Employer by username instead of user object
        employer = Employer.objects.get(username=request.user.username)
        interviews = Interview.objects.filter(job__employer=employer)
    except Employer.DoesNotExist:
        return HttpResponseForbidden("You are not an employer.")

    return render(request, 'employer_interviews.html', {'interviews': interviews})

    

def schedule_interview(request):
    if request.method == 'POST':
        form = InterviewForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('interview_list')  # or wherever you want to go
    else:
        form = InterviewForm()

    return render(request, 'schedule_interview.html', {'form': form})


def create_interview_event(request):
    # Suppose you want to schedule an interview for tomorrow:
    tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)

    # Grab or create a Calendar to hold interviews:
    interview_calendar, created = Calendar.objects.get_or_create(
        slug='interviews', 
        defaults={'name': 'Interviews Calendar'}
    )

    # Create an Event for the candidate:
    candidate = Candidate.objects.get(id=1)  # example
    job_title = "Software Engineer"          # example

    event = Event.objects.create(
        start=tomorrow.replace(hour=10, minute=0),
        end=tomorrow.replace(hour=11, minute=0),
        title=f"Interview - {candidate.user.first_name} ({job_title})",
        creator=request.user,  # or some user
        calendar=interview_calendar
    )

    return redirect('schedule')  # or wherever your schedule is displayed


def interview_detail(request, pk):
    interview = get_object_or_404(Interview, pk=pk)
    return render(request, 'interview_detail.html', {'interview': interview})

def reschedule_interview(request, pk):
    interview = get_object_or_404(Interview, pk=pk)

    if request.method == 'POST':
        # For example, get new date/time from the form
        new_date = request.POST.get('date')
        new_time = request.POST.get('time')
        # Update the interview
        interview.date = new_date
        interview.time = new_time
        interview.save()
        return redirect('interview_detail', pk=interview.pk)
    else:
        return render(request, 'reschedule_interview.html', {'interview': interview})

@user_passes_test(is_employer)

@login_required
def get_interviews(request):
    try:
        employer = Employer.objects.get(username=request.user.username)
        interviews = Interview.objects.filter(job__employer=employer)
    except Employer.DoesNotExist:
        return JsonResponse({"error": "Employer not found"}, status=403)

    events = [
        {
            'id': interview.pk,
            'title': f"Interview: {interview.candidate.user.first_name} {interview.candidate.user.last_name}",
            'start': f"{interview.date}T{interview.time}",
            'url': f"/interview/{interview.pk}/"
        }
        for interview in interviews
    ]

    return JsonResponse(events, safe=False)

@login_required
def edit_company_profile(request):
    try:
        # FIX: Use 'username' instead of 'user'
        employer = Employer.objects.get(username=request.user.username)
    except Employer.DoesNotExist:
        return render(request, "error.html", {"message": "Employer not found"})

    if request.method == "POST":
        form = EmployerProfileForm(request.POST, request.FILES, instance=employer)
        if form.is_valid():
            form.save()
            return redirect("employer_settings")  # Redirect to settings after update
    else:
        form = EmployerProfileForm(instance=employer)

    return render(request, "edit_company_profile.html", {"form": form})

@login_required
def delete_account(request):
    if request.method == "POST":
        employer = Employer.objects.get(user=request.user)
        user = request.user
        employer.delete()  # Delete Employer profile
        user.delete()  # Delete User account
        logout(request)
        return redirect("home_page")  # Redirect to homepage after account deletion

    return render(request, "delete_account.html")