from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from tutorials.models.applicants_models import Applicant, Application
from tutorials.forms.applicants_forms import ApplicantForm, ApplicationForm
from django.contrib.auth.decorators import login_required
from decorators import applicant_only  # Import the decorator
from tutorials.models.employer_models import Job, EmployerNotification, JobTitle, Candidate
from django.contrib.messages import get_messages




@applicant_only
@login_required
def applicants_home_page(request):
    """Show jobs matching applicant preferences."""
    
    applicant = Applicant.objects.filter(user=request.user).first()

    approved_jobs = Job.objects.filter(status__iexact='approved')

    return render(request, 'applicants_home_page.html', {"approved_jobs": approved_jobs})


@applicant_only
@login_required
def applicants_edit_profile(request):
    """ Ensure messages from previous actions (like job creation) are cleared """

    storage = get_messages(request)  # ✅ Clears stored messages
    storage.used = True  # ✅ Mark messages as used to prevent showing old ones

    applicant = get_object_or_404(Applicant, user=request.user)

    if request.method == 'POST':
        form = ApplicantForm(request.POST, request.FILES, instance=applicant, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your changes have been saved.")  # ✅ Only relevant messages will show
            return redirect('applicants-edit-profile')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = ApplicantForm(instance=applicant, user=request.user)

    return render(request, 'applicants_edit_profile.html', {
        'form': form,
        'applicant': applicant,
    })



@login_required
def applicants_applied_jobs(request):
    """ Display jobs that the logged-in applicant has applied to """

    # ✅ Fetch applications for the logged-in user
    applicant = get_object_or_404(Applicant, user=request.user)
    applied_jobs = Application.objects.filter(applicant=applicant).select_related('job')


    return render(request, 'applicants_applied_jobs.html', {
        'applied_jobs': applied_jobs,
    })


@applicant_only
def applicants_favourites(request):
    return render(request, 'applicants_favourites.html')

@applicant_only
def applicants_notifications(request):
    notifications = [
        {"title": "Interview Scheduled", "message": "Your interview with XYZ Corp is scheduled for tomorrow.", "timestamp": "2025-02-18 10:00 AM"},
        {"title": "Job Application Update", "message": "Your application for the Software Engineer role at ABC Ltd. has been viewed.", "timestamp": "2025-02-17 05:00 PM"},
    ]
    
    return render(request, 'applicants_notifications.html', {'notifications': notifications})

@applicant_only
def applicants_account(request):
    applicant = get_object_or_404(Applicant, user=request.user)
    return render(request, 'applicants_account.html', {
        'applicant': applicant,
        # you can also pass user if you want {{ user.first_name }} in the template
        'user': request.user,
    })

@applicant_only
def applicants_analytics(request):
    return render(request, 'applicants_analytics.html')



@login_required
def job_detail(request, job_id):
    """Display job details and check if the user has applied"""
    job = get_object_or_404(Job, id=job_id)
    applicant = Applicant.objects.filter(user=request.user).first()

    # Check if the user has already applied
    existing_application = False
    if applicant:
        existing_application = Application.objects.filter(applicant=applicant, job=job).exists()

    return render(request, "job_detail.html", {
        "job": job,
        "existing_application": existing_application
    })

import logging

logger = logging.getLogger(__name__)

@login_required
def apply_for_job(request, job_id):
    """Handles job application submission, preventing duplicate applications"""
    
    job = get_object_or_404(Job, id=job_id)
    applicant = get_object_or_404(Applicant, user=request.user)

    # ✅ Check if the applicant has already applied for this job
    existing_application = Application.objects.filter(applicant=applicant, job=job).exists()

    if existing_application:
        messages.warning(request, "You have already applied for this job.")
        return redirect("job_detail", job_id=job.id)  # Redirect to job detail page

    if request.method == "POST":
        form = ApplicationForm(request.POST, request.FILES)

        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.applicant = applicant  # ✅ Assign the applicant
            application.save()

            # ✅ Debugging logs
            logger.info(f"Creating candidate for {applicant.user.username} for job {job.title}")

            # ✅ Create a Candidate entry to be listed under employer's candidates
            candidate, created = Candidate.objects.get_or_create(
                user=applicant.user,  # ✅ Link to the user
                job=job,              # ✅ Link to the job they applied for
                defaults={
                    "resume": form.cleaned_data.get("resume"),
                    "cover_letter": form.cleaned_data.get("cover_letter"),
                    "application_status": "Pending"
                }
            )

            if created:
                logger.info(f"✅ Candidate created for {applicant.user.username} and job {job.title}")
            else:
                logger.warning(f"⚠️ Candidate already existed for {applicant.user.username} and job {job.title}")

            # ✅ Create an employer notification for new application
            EmployerNotification.objects.create(
                employer=job.employer,
                title="New Job Application",  
                message=f"📩 New application received for {job.title} by {applicant.user.first_name} {applicant.user.last_name}!"
            )

            messages.success(request, "✅ Your application has been submitted successfully!")
            return redirect("job_detail", job_id=job.id)  # Redirect to job detail page

    else:
        form = ApplicationForm()

    return render(request, "applicants_application.html", {"form": form, "job": job, "existing_application": existing_application})
