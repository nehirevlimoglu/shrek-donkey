from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from tutorials.models.applicants_models import Applicant, Application, ApplicantNotification
from tutorials.forms.applicants_forms import ApplicantForm, ApplicationForm
from django.contrib.auth.decorators import login_required
from decorators import applicant_only  # Import the decorator
from tutorials.models.employer_models import Job, EmployerNotification, JobTitle, Candidate
from django.contrib.messages import get_messages
from django.contrib import messages
from django.http import JsonResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


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
@login_required
def applicants_notifications(request):
    applicant = get_object_or_404(Applicant, user=request.user)
    notifications = ApplicantNotification.objects.filter(applicant=applicant).order_by('-timestamp')
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

    # ✅ Fix: Ensure `existing_application` is correctly set
    existing_application = Application.objects.filter(applicant=applicant, job=job).exists() if applicant else False

    return render(request, "job_detail.html", {
        "job": job,
        "existing_application": existing_application
    })

@csrf_exempt  # ✅ Bypass CSRF for AJAX requests
@applicant_only
@login_required
def apply_for_job(request, job_id):
    """Handles job application submission, preventing duplicate applications"""
    job = get_object_or_404(Job, id=job_id)
    applicant = get_object_or_404(Applicant, user=request.user)

    existing_application = Application.objects.filter(applicant=applicant, job=job).exists()
    if existing_application:
        return JsonResponse({"success": False, "error": "You have already applied for this job."})

    if request.method == "POST":
        application = Application.objects.create(
            job=job,
            applicant=applicant,
            resume=None,  
            cover_letter=None,
        )

        # Notify employer
        EmployerNotification.objects.create(
            employer=job.employer,
            title="New Job Application",
            message=f"📩 New application received for {job.title} by {applicant.user.first_name} {applicant.user.last_name}!"
        )

        # Notify applicant
        ApplicantNotification.objects.create(
            applicant=applicant,
            title="Application Submitted",
            message=f"Your application for '{job.title}' has been submitted successfully!"
        )

        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "error": "Invalid request method."})


@applicant_only
@login_required
def applicants_notifications(request):
    """Display real notifications for the logged-in applicant"""
    applicant = get_object_or_404(Applicant, user=request.user)
    notifications = ApplicantNotification.objects.filter(applicant=applicant).order_by('-timestamp')

    return render(request, 'applicants_notifications.html', {'notifications': notifications})