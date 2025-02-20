from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from tutorials.models.applicants_models import Applicant 
from tutorials.forms.applicants_forms import ApplicantForm 
from django.contrib.auth.decorators import login_required
from decorators import applicant_only  # Import the decorator

@applicant_only
def applicants_home_page(request):
    return render(request, 'applicants_home_page.html')

@applicant_only
def applicants_account(request, applicant_id=None):
    applicant = get_object_or_404(Applicant, id=applicant_id) if applicant_id else Applicant.objects.first()

    if request.method == "POST":
        form = ApplicantForm(request.POST, request.FILES, instance=applicant)
        if form.is_valid():
            form.save()
            messages.success(request, "Your account has been updated successfully!")
            return redirect('applicants-account')
        else:
            messages.error(request, "There was an error saving your account information.")
    else:
        form = ApplicantForm(instance=applicant)

    return render(request, "applicants_account.html", {"form": form, "applicant": applicant})

@applicant_only
def applicants_applied_jobs(request):
    return render(request, 'applicants_applied_jobs.html')

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
