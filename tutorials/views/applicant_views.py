from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from tutorials.models.applicants_models import Applicant, Application
from tutorials.forms.applicants_forms import ApplicantForm, ApplicationForm
from django.contrib.auth.decorators import login_required
from decorators import applicant_only  # Import the decorator
from tutorials.models.employer_models import Job, EmployerNotification
from tutorials.models.employer_models import Job, JobTitle
from django.contrib.messages import get_messages




@applicant_only
@login_required
def applicants_home_page(request):
    """Show jobs matching applicant preferences."""
    
    applicant = Applicant.objects.filter(user=request.user).first()

    if applicant:
        preferred_titles = list(applicant.job_preferences.values_list('title', flat=True))
        approved_jobs = Job.objects.filter(status="approved", title__in=preferred_titles)

    else:
        approved_jobs = Job.objects.filter(status="approved")

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
def apply_for_job(request, job_id):
    """Handles job application submission"""
    
    job = get_object_or_404(Job, id=job_id)
    applicant = request.user  # ✅ Ensure the logged-in user is set as the applicant

    if request.method == "POST":
        form = ApplicationForm(request.POST, request.FILES)

        if form.is_valid():
            application = form.save(commit=False)
            application.job = job  # ✅ Assign the job to the application
            applicant = get_object_or_404(Applicant, user=request.user)  # Get the correct applicant


            application.save()

            # ✅ Create an employer notification for new application
            EmployerNotification.objects.create(
                employer=job.employer,
                title="New Job Application",  # Ensure a title is provided
                message=f"📩 New application received for {job.title} by {applicant.user.first_name} {applicant.user.last_name}!"
            )


            messages.success(request, "✅ Your application has been submitted successfully!")
            return redirect("applicants-home-page")

    else:
        form = ApplicationForm()

    return render(request, "applicants_application.html", {"form": form, "job": job})
