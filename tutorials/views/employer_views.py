from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseRedirect
from tutorials.models.employer_models import Employer, Job, Candidate, Interview, EmployerNotification, EmployerEvent
from tutorials.models.admin_models import Notification 
from tutorials.forms.forms import SignUpForm, LogInForm
from tutorials.forms.employer_forms import JobForm, EmployerProfileForm, CustomPasswordChangeForm, InterviewForm
from tutorials.forms.forms import CustomPasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.http import JsonResponse, HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.http import HttpResponseForbidden
import logging, json
from tutorials.models.applicants_models import Application, ApplicantNotification, Applicant
from django.utils.dateparse import parse_date, parse_time
from django.utils.timezone import now
from django.db.models import Count, Q
from django.core.serializers.json import DjangoJSONEncoder

from django.http import HttpResponseRedirect
from django.urls import reverse
from tutorials.utils import match_candidates_to_job
from datetime import datetime, date

logger = logging.getLogger(__name__)

def is_employer(user):
    return hasattr(user, 'role') and user.role == 'Employer'

@login_required
def employer_home_page(request):
    """Employer dashboard with statistics, notifications & recent applicants"""

    try:
        employer = Employer.objects.get(username=request.user.username)

        # ✅ Fetch notifications
        notifications = EmployerNotification.objects.filter(employer=employer).order_by('-created_at')
        notifications.update(is_read=True)

        # ✅ Fetch recent applicants (only those who applied to this employer's jobs)
        recent_applicants = Candidate.objects.filter(
            job__employer=employer
        ).select_related('job', 'user').order_by('-application_date')[:10]

        # ✅ Fetch Analytics Data
        total_jobs = Job.objects.filter(employer=employer).count()
        active_listings = Job.objects.filter(
            employer=employer, 
            application_deadline__gte=now()  # ✅ Only count jobs with valid deadlines
        ).count()
        total_applicants = Candidate.objects.filter(job__employer=employer).count()  # ✅ Fix: Count applicants for employer's jobs

    except Employer.DoesNotExist:
        return JsonResponse({"success": False, "error": "Employer profile not found"}, status=403)

    return render(request, 'employers_home_page.html', {
        'notifications': notifications,
        'recent_applicants': recent_applicants,
        'total_jobs': total_jobs,  # ✅ Pass total jobs
        'active_listings': active_listings,  # ✅ Pass active job count
        'total_applicants': total_applicants,  # ✅ Pass total applicants
    })

@login_required
def view_employer_analytics(request):
    """Fetch employer analytics data for reporting."""
    try:
        employer = Employer.objects.get(username=request.user.username)

        # ✅ Fetch core analytics data
        total_jobs = Job.objects.filter(employer=employer).count()
        total_applicants = Candidate.objects.filter(job__employer=employer).count()

        # ✅ Count of scheduled interviews that have not been completed
        pending_interviews = Interview.objects.filter(
            job__employer=employer, date__gte=now().date()
        ).count()

        average_apps_per_job = total_applicants / total_jobs if total_jobs > 0 else 0

        # ✅ Fetch job-wise analytics
        job_analytics = Job.objects.filter(employer=employer).annotate(
            applicants=Count("candidates"),
            interviews=Count("job_interviews"),
            hires=Count("candidates", filter=Q(candidates__application_status="Hired"))
        )

        job_data = []
        job_titles = []
        job_applicants = []
        job_interviews = []

        for job in job_analytics:
            job_titles.append(job.title)
            job_applicants.append(job.applicants)
            job_interviews.append(job.interviews)
            job_data.append({
                "title": job.title,
                "applicants": job.applicants,
                "interviews": job.interviews,
                "hires": job.hires,
            })

    except Employer.DoesNotExist:
        return render(request, 'employer_analytics.html', {
            "error": "Employer profile not found"
        })

    return render(request, 'employer_analytics.html', {
        'total_jobs': total_jobs,
        'total_applicants': total_applicants,
        'average_apps_per_job': round(average_apps_per_job, 1),
        'pending_interviews': pending_interviews,  # ✅ Scheduled but not yet completed interviews
        'job_analytics': job_data,  # ✅ Pass job-specific analytics
        'job_titles': json.dumps(job_titles, cls=DjangoJSONEncoder),  # ✅ Convert to JSON
        'job_applicants': json.dumps(job_applicants, cls=DjangoJSONEncoder),  # ✅ Convert to JSON
        'job_interviews': json.dumps(job_interviews, cls=DjangoJSONEncoder),  # ✅ Convert to JSON
    })

@login_required
def employer_settings(request):
    return render(request, 'employer_settings.html')


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
            job.employer = employer

            # Handle location + company name defaults
            form_location = form.cleaned_data.get('location')
            job.location = form_location or employer.company_location or "Unknown Location"
            job.company_name = employer.company_name or "Unknown Company"
            job.contact_email = employer.email or "no-email@company.com"

            job.save()  # ✅ This will call form.save(), which triggers skill extraction

            messages.success(request, "🎉 Job listing created successfully!")
            return redirect('employer_job_listings')
        else:
            messages.error(request, "There was an error with your submission.")
            logger.error("❌ Job form is invalid!")
    else:
        form = JobForm()

    return render(request, 'employer_create_job_listing.html', {'form': form})


def job_detail_view(request, job_id):
    job = get_object_or_404(Job, id=job_id)  # ✅ Correct

    return render(request, 'job_detail.html', {'job': job})


def edit_job_view(request, pk):
    job = get_object_or_404(Job, pk=pk)

    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            return redirect('employer_job_detail', job_id=job.pk)  # ✅ FIXED: use job_id
    else:
        form = JobForm(instance=job)

    return render(request, 'edit_job.html', {'form': form, 'job': job})




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
    """Retrieve all candidates who applied for jobs posted by the employer, with filtering options."""
    try:
        employer = Employer.objects.get(username=request.user.username)
    except Employer.DoesNotExist:
        return HttpResponseForbidden("You are not authorized to view this page.")

    # ✅ Get all jobs posted by this employer
    employer_jobs = Job.objects.filter(employer=employer)

    # ✅ Retrieve all candidates who applied to these jobs
    candidates = Candidate.objects.filter(job__in=employer_jobs).select_related('user', 'job')

    # ✅ Get distinct degrees from candidates for the dropdown
    degrees = Candidate.objects.exclude(degree__isnull=True).exclude(degree="").values_list('degree', flat=True).distinct()

    # ✅ Filtering
    job_id = request.GET.get("job")  # Job filter
    status = request.GET.get("status")  # Application status filter
    degree = request.GET.get("degree")  # Degree filter

    if job_id:
        candidates = candidates.filter(job_id=job_id)

    if status:
        candidates = candidates.filter(application_status=status)

    if degree:
        candidates = candidates.filter(degree=degree)

    return render(request, 'employer_candidates.html', {
        'candidates': candidates,
        'jobs': employer_jobs,  # Pass job listings for dropdown
        'statuses': Candidate.STATUS_CHOICES,  # Pass statuses for dropdown
        'degrees': degrees,  # Pass degrees for dropdown
    })

@login_required
def employer_calendar(request):
    if not hasattr(request.user, 'employer'):
        return HttpResponseForbidden("You are not an employer.")

    employer = request.user.employer
    interviews = Interview.objects.filter(job__employer=employer)
    return render(request, 'employer_calendar.html', {'interviews': interviews})



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
        employer.delete() 
        user.delete()  
        logout(request)
        return redirect("log_in")  

    return render(request, "delete_account.html")



@login_required
def employer_job_listings(request):
    """Display only the jobs posted by the logged-in employer and attach matched candidates to each job."""

    try:
        employer = Employer.objects.get(username=request.user.username)
    except Employer.DoesNotExist:
        return render(request, 'error.html', {"message": "Employer profile not found."})

    jobs = Job.objects.filter(employer=employer)

    if not jobs.exists():
        logger.warning(f"⚠️ No jobs found for employer: {employer.company_name}")

    # For each job, run the matching function and attach the results
    for job in jobs:
        matched = match_candidates_to_job(job.title, top_n=5)
        # If the function returns a string, it might be an error message, so handle that:
        if isinstance(matched, list):
            job.matched_candidates = matched  # A list of (candidate, score) tuples
        else:
            # It's a string (e.g., an error message or "No candidates")
            job.matched_candidates = []

    return render(request, 'employer_job_listings.html', {'jobs': jobs})


@login_required
def employer_notifications(request):
    try:
        employer = Employer.objects.get(user=request.user)
    except Employer.DoesNotExist:
        return JsonResponse({"success": False, "error": "Employer profile not found"}, status=403)

    notifications = EmployerNotification.objects.filter(employer=employer).order_by('-created_at')

    return render(request, 'employer_notifications.html', {
        'notifications': notifications
    })


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


def calculate_duration(start_date, end_date):
    """
    Calculate the duration between start_date and end_date.
    If end_date is missing or 'Present', use today's date.
    Returns a string like "X years, Y months, Z days".
    """
    if not start_date:
        return ""
    
    # Convert start_date to a date object if necessary.
    if isinstance(start_date, str):
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            return ""
    
    # Process end_date: if empty or "Present", use today's date.
    if not end_date or end_date == "Present":
        end_date = date.today()
    elif isinstance(end_date, str):
        try:
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            end_date = date.today()
    
    delta = end_date - start_date
    total_days = delta.days
    years = total_days // 365
    months = (total_days % 365) // 30
    days = (total_days % 365) % 30
    return f"{years} years, {months} months, {days} days"


@login_required
def applicant_profile(request, applicant_id):
    """View full applicant details for an employer."""
    try:
        # Get the candidate instance (used in employer views)
        candidate = Candidate.objects.get(id=applicant_id)
    except Candidate.DoesNotExist:
        return HttpResponse("Candidate does not exist.", status=404)
    
    try:
        # Retrieve the Applicant instance linked to the candidate's user
        applicant_obj = Applicant.objects.get(user=candidate.user)
    except Applicant.DoesNotExist:
        return HttpResponse("Applicant profile not found.", status=404)
    
    try:
        # Retrieve the Application instance for this applicant and job
        application = Application.objects.get(applicant=applicant_obj, job=candidate.job)
    except Application.DoesNotExist:
        application = None  # Handle as needed
    
    # Add duration info to each work experience entry if available.
    if application and application.work_experience:
        for work in application.work_experience:
            work['duration'] = calculate_duration(work.get('work_start_date'), work.get('work_end_date'))
    
    # Handle status update submissions.
    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in ["Pending", "Interview", "Hired", "Rejected"]:
            candidate.application_status = new_status
            candidate.save()
            messages.success(request, "Application status updated successfully!")
        return redirect("applicant_profile", applicant_id=candidate.id)
    
    return render(request, "applicant_profile.html", {
        "candidate": candidate,
        "application": application
    })

@csrf_exempt
@login_required
def mark_notification_as_read(request, notification_id):
    try:
        employer = Employer.objects.get(user=request.user)
        notification = EmployerNotification.objects.get(id=notification_id, employer=employer)

        if request.method == "POST":
            notification.is_read = True
            notification.save()
            return JsonResponse({"success": True})

        return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)

    except Employer.DoesNotExist:
        return JsonResponse({"success": False, "error": "Employer not found"}, status=403)
    except EmployerNotification.DoesNotExist:
        return JsonResponse({"success": False, "error": "Notification not found"}, status=404)


@login_required
def schedule_interview(request, applicant_id):
    """Page for scheduling an interview with a candidate"""
    try:
        applicant = Candidate.objects.get(id=applicant_id)
    except Candidate.DoesNotExist:
        return HttpResponse("Candidate does not exist.", status=404)

    if request.method == "POST":
        # 1 Grab form data
        interview_date = request.POST.get('interview_date')
        interview_time = request.POST.get('interview_time')
        interview_link = request.POST.get('interview_link')
        notes = request.POST.get('notes')

        # 2 Parse date/time from string
        try:
            interview_date = parse_date(interview_date)
            interview_time = parse_time(interview_time)
        except ValueError:
            return HttpResponse("Invalid date or time format.", status=400)
        
        # 3) Create the interview
        interview = Interview.objects.create(
            candidate=applicant,
            job=applicant.job,
            date=interview_date,
            time=interview_time,
            interview_link=interview_link,
            notes=notes,
        )
        #interview.save()

        # 4 Create an ApplicantNotification for the actual applicant
        #    The Candidate model references user=User. We need to find the `Applicant` object that belongs to that user.
        try:
            applicant_obj = Applicant.objects.get(user=applicant.user)

            ApplicantNotification.objects.create(
                applicant=applicant_obj,
                title="Interview Scheduled",
                message=(
                    f"Your interview for '{applicant.job.title}' has been scheduled "
                    f"on {interview_date} at {interview_time}.\n\n"
                    f"Link/Location: {interview_link if interview_link else 'See employer message'}\n"
                    f"Additional Notes: {notes or 'N/A'}"
                )
            )

        except Applicant.DoesNotExist:
            logger.warning(f"No matching Applicant found for user {applicant.user.username}. Cannot create notification.")

        # 5 Redirect or render as you wish
        messages.success(request, "Interview scheduled successfully!")
        return redirect('employer_calendar')

    else:
        return render(request, 'schedule_interview.html', {'applicant': applicant})


@csrf_exempt
@login_required
def accept_candidate(request, candidate_id):
    candidate = get_object_or_404(Candidate, id=candidate_id)

    if candidate.application_status in ["Hired", "Rejected"]:
        return JsonResponse({"error": "Status cannot be changed once set."}, status=400)

    candidate.application_status = "Hired"
    candidate.save()

    try:
        applicant_obj = Applicant.objects.get(user=candidate.user)
        employer_email = candidate.job.employer.email if candidate.job.employer and candidate.job.employer.email else "contact@example.com"

        # ✅ Update the Application status to "hired"
        application = Application.objects.get(applicant=applicant_obj, job=candidate.job)
        application.status = "hired"
        application.save()

        ApplicantNotification.objects.create(
            applicant=applicant_obj,
            title="Congratulations, You're Hired!",
            message=(
                f"You have been hired for the {candidate.job.title} position. "
                f"Please contact {employer_email} for further details."
            )
        )
    except (Applicant.DoesNotExist, Application.DoesNotExist):
        logger.warning(f"Could not update Application for hired candidate {candidate.id}")

    return JsonResponse({"message": "Candidate accepted successfully!", "status": "Hired"})


@csrf_exempt
@login_required
def reject_candidate(request, candidate_id):
    candidate = get_object_or_404(Candidate, id=candidate_id)

    if candidate.application_status in ["Hired", "Rejected"]:
        return JsonResponse({"error": "Status cannot be changed once set."}, status=400)

    candidate.application_status = "Rejected"
    candidate.save()

    try:
        applicant_obj = Applicant.objects.get(user=candidate.user)
        application = Application.objects.get(applicant=applicant_obj, job=candidate.job)
        application.status = "rejected"
        application.save()
    except (Applicant.DoesNotExist, Application.DoesNotExist):
        logger.warning(f"Could not update Application for rejected candidate {candidate.id}")

    return JsonResponse({"message": "Candidate rejected successfully!", "status": "Rejected"})
