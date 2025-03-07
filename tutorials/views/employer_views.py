from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from tutorials.models.employer_models import Employer, Job, Candidate, Interview, EmployerNotification, EmployerEvent
from tutorials.models.admin_models import Notification 
from tutorials.forms.forms import SignUpForm, LogInForm
from tutorials.forms.employer_forms import JobForm, EmployerProfileForm
from tutorials.forms.forms import CustomPasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.http import HttpResponseForbidden
import logging
from tutorials.models.applicants_models import Application

def is_employer(user):
    return hasattr(user, 'role') and user.role == 'Employer'

@login_required
def employer_home_page(request):
    """Employer dashboard with notifications & recent applicants"""

    try:
        employer = Employer.objects.get(username=request.user.username)

        # ✅ Fetch notifications
        notifications = EmployerNotification.objects.filter(employer=employer).order_by('-created_at')

        # ✅ Fetch recent applicants (only those who applied to this employer's jobs)
        recent_applicants = Candidate.objects.filter(
            job__employer=employer
        ).select_related('job', 'user').order_by('-application_date')[:10]


    except Employer.DoesNotExist:
        return JsonResponse({"success": False, "error": "Employer profile not found"}, status=403)

    return render(request, 'employers_home_page.html', {
        'notifications': notifications,
        'recent_applicants': recent_applicants  # ✅ Pass the recent applicants to the template
    })




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
    """ Display only the jobs posted by the logged-in employer """
    
    employer = getattr(request.user, 'employer', None)  # ✅ Fetch employer if exists
    jobs = Job.objects.filter(employer=employer) if employer else []  # ✅ Get jobs posted by this employer

    return render(request, 'employer_job_listings.html', {'jobs': jobs})




logger = logging.getLogger(__name__)

@login_required
def create_job_listings(request):
    """ Allow employers to create job listings while handling missing employer profiles. """

    try:
        employer = Employer.objects.get(username=request.user.username)
    except Employer.DoesNotExist:
        messages.error(request, "You must be an employer to post a job.")
        return redirect('employer_home_page')

    if request.method == 'POST':
        form = JobForm(request.POST)

        if form.is_valid():
            job = form.save(commit=False)
            job.employer = employer  # ✅ Associate job with employer
            
            # ✅ Ensure job location and company name are correctly set
            form_location = form.cleaned_data.get('location')
            employer_location = employer.company_location
            job.location = form_location if form_location else employer_location if employer_location else "Unknown Location"

            job.company_name = employer.company_name if employer.company_name else "Unknown Company"
            job.contact_email = employer.email if employer.email else "no-email@company.com"
            job.save()

            logger.info(f"✅ Job created successfully: {job.title} - {job.location}")

            messages.success(request, "🎉 Job listing created successfully!")
            return redirect('employer_job_listings')
        else:
            messages.error(request, "There was an error with your submission.")
            logger.error("❌ Job form is invalid!")
    else:
        form = JobForm()

    return render(request, 'employer_create_job_listing.html', {'form': form})



def job_detail_view(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    return render(request, 'job_detail.html', {'job': job})

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
    """Retrieve all candidates who applied for jobs posted by the employer"""
    try:
        employer = Employer.objects.get(username=request.user.username)
    except Employer.DoesNotExist:
        return HttpResponseForbidden("You are not authorized to view this page.")

    # ✅ Get all jobs posted by this employer
    employer_jobs = Job.objects.filter(employer=employer)

    # ✅ Retrieve all candidates who applied to these jobs
    candidates = Candidate.objects.filter(job__in=employer_jobs).select_related('user', 'job')

    print("Employer:", employer)
    print("Jobs posted by employer:", employer_jobs)
    print("Candidates who applied:", candidates.values())

    return render(request, 'employer_candidates.html', {
        'candidates': candidates,
    })



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
        employer.delete() 
        user.delete()  
        logout(request)
        return redirect("home_page")  

    return render(request, "delete_account.html")



@login_required
def employer_job_listings(request):
    """ Display only the jobs posted by the logged-in employer """

    try:
        employer = Employer.objects.get(username=request.user.username)
    except Employer.DoesNotExist:
        return render(request, 'error.html', {"message": "Employer profile not found."})

    jobs = Job.objects.filter(employer=employer)

    if not jobs.exists():
        logger.warning(f"⚠️ No jobs found for employer: {employer.company_name}")

    return render(request, 'employer_job_listings.html', {'jobs': jobs})


@login_required
def employer_notifications(request):
    """Display notifications for the logged-in employer."""
    employer = request.user  # The employer who is logged in
    notifications = Notification.objects.filter(recipient=employer).order_by('-created_at')

    # Mark notifications as read when viewed
    notifications.update(is_read=True)

    return render(request, 'employer_notifications.html', {'notifications': notifications})

@login_required
def get_employer_events(request):
    """Fetch events only for the logged-in employer"""
    try:
        employer = Employer.objects.get(username=request.user.username)  # Get employer using username
        events = EmployerEvent.objects.filter(employer=employer)

        event_list = [
            {
                "id": event.id,
                "title": event.title,
                "start": event.start.strftime('%Y-%m-%dT%H:%M:%S'),
                "end": event.end.strftime('%Y-%m-%dT%H:%M:%S') if event.end else None,
            }
            for event in events
        ]

        return JsonResponse(event_list, safe=False)

    except Employer.DoesNotExist:
        return JsonResponse({"error": "Employer not found"}, status=403)

@login_required
def review_application(request, application_id):
    """Display full application details"""
    application = get_object_or_404(Application, id=application_id)
    
    return render(request, "application_review.html", {"application": application})


@csrf_exempt
@login_required
def mark_notification_as_read(request, notification_id):
    """Marks an employer's notification as read"""
    try:
        employer = Employer.objects.get(username=request.user.username)  # Ensure we fetch the employer
        notification = EmployerNotification.objects.get(id=notification_id, employer=employer)  # Use 'employer'

        notification.is_read = True
        notification.save()

        return JsonResponse({"success": True})
    except EmployerNotification.DoesNotExist:
        return JsonResponse({"success": False, "error": "Notification not found"}, status=404)
    except Employer.DoesNotExist:
        return JsonResponse({"success": False, "error": "Employer profile not found"}, status=403)


@login_required
def applicant_profile(request, applicant_id):
    """View full applicant details"""
    
    print(f"Requested Applicant ID: {applicant_id}")  # Debugging line

    try:
        applicant = Candidate.objects.get(id=applicant_id)  # Get the candidate
        print(f"Applicant Found: {applicant}")  # Debugging line
    except Candidate.DoesNotExist:
        return HttpResponse("Candidate does not exist.", status=404)  # Explicit error message

    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in ["Pending", "Interview", "Hired", "Rejected"]:
            applicant.application_status = new_status
            applicant.save()
            messages.success(request, "Application status updated successfully!")
        return redirect("applicant_profile", applicant_id=applicant.id)

    return render(request, "applicant_profile.html", {"applicant": applicant})
    
@login_required
def schedule_interview(request, applicant_id):
    """Page for scheduling an interview with a candidate"""
    try:
        applicant = Candidate.objects.get(id=applicant_id)
    except Candidate.DoesNotExist:
        return HttpResponse("Candidate does not exist.", status=404)

    return render(request, "schedule_interview.html", {"applicant": applicant})