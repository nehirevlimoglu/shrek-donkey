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

@applicant_only
def applicants_account(request):
    applicant = get_object_or_404(Applicant, user=request.user)
    return render(request, 'applicants_account.html', {
        'applicant': applicant,
        # you can also pass user if you want {{ user.first_name }} in the template
        'user': request.user,
    })