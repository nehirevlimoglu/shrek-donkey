from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from tutorials.models.applicants_models import Applicant, Application
from tutorials.forms.applicants_forms import ApplicantForm, ApplicationForm
from django.contrib.auth.decorators import login_required
from decorators import applicant_only  # Import the decorator
from tutorials.models.employer_models import Job, EmployerNotification





@applicant_only

def applicants_home_page(request):
    """Applicants homepage displaying only approved jobs."""
    
    approved_jobs = Job.objects.filter(status__iexact="approved")
    
    print("🔍 DEBUG: Fetching approved jobs from the database...")
    print(f"🔎 Found {approved_jobs.count()} approved jobs")  # ✅ Log job count
    
    for job in approved_jobs:
        print(f"✅ Job: {job.title} | Company: {job.company_name} | Status: {job.status}")

    return render(request, 'applicants_home_page.html', {"approved_jobs": approved_jobs})


@applicant_only
@login_required
def applicants_edit_profile(request):
    applicant = get_object_or_404(Applicant, user=request.user)
    
    if request.method == 'POST':
        form = ApplicantForm(request.POST, request.FILES, instance=applicant, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your changes have been saved.")
            return redirect('applicants-edit-profile')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        # Make sure to pass user=request.user on GET requests
        form = ApplicantForm(instance=applicant, user=request.user)

    return render(request, 'applicants_edit_profile.html', {
        'form': form,
        'applicant': applicant,
    })


@login_required
def applicants_applied_jobs(request):
    """ Display jobs that the logged-in applicant has applied to """

    # ✅ Fetch applications for the logged-in user
    applied_jobs = Application.objects.filter(applicant=request.user).select_related('job')

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
def apply_for_job(request, job_id):
    """Handles job application submission"""
    
    job = get_object_or_404(Job, id=job_id)
    applicant = request.user  # ✅ Ensure the logged-in user is set as the applicant

    if request.method == "POST":
        form = ApplicationForm(request.POST, request.FILES)

        if form.is_valid():
            application = form.save(commit=False)
            application.job = job  # ✅ Assign the job to the application
            application.applicant = applicant  # ✅ Assign the logged-in user

            application.save()

            # ✅ Create an employer notification for new application
            EmployerNotification.objects.create(
                employer=job.employer,
                message=f"📩 New application received for {job.title} by {applicant.first_name} {applicant.last_name}!"
            )

            messages.success(request, "✅ Your application has been submitted successfully!")
            return redirect("applicants-home-page")

    else:
        form = ApplicationForm()

    return render(request, "applicants_application.html", {"form": form, "job": job})
