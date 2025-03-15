from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages  # Import the messages module
from tutorials.models.applicants_models import Applicant, Application, ApplicantNotification
from tutorials.forms.applicants_forms import ApplicantForm, ApplicationForm
from django.contrib.auth.decorators import login_required
from decorators import applicant_only  # Import the decorator
from tutorials.models.employer_models import Job, EmployerNotification, JobTitle, Candidate
from django.contrib.messages import get_messages



@applicant_only
@login_required
def applicants_home_page(request):
    applicant = Applicant.objects.filter(user=request.user).first()
    jobs = Job.objects.filter(status__iexact='approved')

    location = request.GET.get('location')
    salary_interval = request.GET.get('salary_interval')
    job_type = request.GET.get('job_type')
    company = request.GET.get('company')

    new_applicant = request.GET.get('newUser') == "true"  # ✅ Capture newUser param

    if location:
        jobs = jobs.filter(location__iexact=location)
    
    if salary_interval:
        try:
            lower, upper = salary_interval.split('-')
            jobs = jobs.filter(salary__gte=lower, salary__lte=upper)
        except ValueError:
            pass

    if job_type:
        job_type_mapping = {
            "full-time": "Full Time",
            "part-time": "Part Time",
            "internship": "Internship",
            "apprenticeship": "Apprenticeship"
        }
        formatted_job_type = job_type_mapping.get(job_type.strip().lower())
        if formatted_job_type:
            jobs = jobs.filter(job_type__iexact=formatted_job_type)

    if company:
        jobs = jobs.filter(company_name__iexact=company)

    # Get the list of unique companies from approved jobs
    companies = Job.objects.filter(status__iexact='approved') \
                           .values_list('company_name', flat=True).distinct()

    # Get the list of unique locations from approved jobs
    locations = Job.objects.filter(status__iexact='approved') \
                           .values_list('location', flat=True).distinct()

    print(f"🔍 new_applicant (Django) = {new_applicant}")  # Debugging

    return render(request, 'applicants_home_page.html', {
        "approved_jobs": jobs,
        "companies": companies,  # for company filter
        "locations": locations,  # for location filter
        "new_applicant": new_applicant  # ✅ Pass to template
    })



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

    # Check if the user has already applied
    existing_application = False
    if applicant:
        existing_application = Application.objects.filter(applicant=applicant, job=job).exists()

    return render(request, "job_detail.html", {
        "job": job,
        "existing_application": existing_application
    })

import logging

@login_required
def apply_for_job(request, job_id):
    """Handles job application submission, preventing duplicate applications"""
    job = get_object_or_404(Job, id=job_id)
    applicant = get_object_or_404(Applicant, user=request.user)

    existing_application = Application.objects.filter(applicant=applicant, job=job).exists()
    if existing_application:
        messages.warning(request, "You have already applied for this job.")
        return redirect("job_detail", job_id=job.id)

    if request.method == "POST":
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.applicant = applicant
            application.save()

            # Save or update Candidate entry
            candidate, created = Candidate.objects.update_or_create(
                user=applicant.user,
                job=job,
                defaults={
                    "resume": form.cleaned_data.get("resume"),
                    "cover_letter": form.cleaned_data.get("cover_letter"),
                    "first_name": form.cleaned_data.get("first_name"),
                    "last_name": form.cleaned_data.get("last_name"),
                    "phone": form.cleaned_data.get("phone"),
                    "address": form.cleaned_data.get("address"),
                    
                    # Education fields
                    "school": form.cleaned_data.get("school"),
                    "degree": form.cleaned_data.get("degree"),
                    "discipline": form.cleaned_data.get("discipline"),
                    "start_date": form.cleaned_data.get("start_date"),
                    "end_date": form.cleaned_data.get("end_date"),
                    
                    "linkedin_profile": form.cleaned_data.get("linkedin_profile"),
                    "portfolio_website": form.cleaned_data.get("portfolio_website"),
                    "how_did_you_hear": form.cleaned_data.get("how_did_you_hear"),
                    "current_job_title": form.cleaned_data.get("current_job_title"),
                    "current_employer": form.cleaned_data.get("current_employer"),
                    "application_status": "Pending"
                }
            )



            # Create an EmployerNotification
            EmployerNotification.objects.create(
                employer=job.employer,
                title="New Job Application",  
                message=f"📩 New application received for {job.title} by {applicant.user.first_name} {applicant.user.last_name}!"
            )

            # Create an ApplicantNotification
            ApplicantNotification.objects.create(
                applicant=applicant,
                title="Application Submitted",
                message=f"Your application for '{job.title}' has been submitted successfully!"
            )

            messages.success(request, "✅ Your application has been submitted successfully!")
            return redirect("job_detail", job_id=job.id)
    else:
        form = ApplicationForm()

    return render(request, "applicants_application.html", {"form": form, "job": job, "existing_application": existing_application})


@applicant_only
@login_required
def applicants_notifications(request):
    """Display real notifications for the logged-in applicant"""
    applicant = get_object_or_404(Applicant, user=request.user)
    notifications = ApplicantNotification.objects.filter(applicant=applicant).order_by('-timestamp')

    return render(request, 'applicants_notifications.html', {'notifications': notifications})