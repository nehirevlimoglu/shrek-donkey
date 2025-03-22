from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages  # Import the messages module
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
from tutorials.utils import extract_skills_nlp
from random import randint
import json
from tutorials.models.employer_models import Interview

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


@login_required
def job_detail(request, job_id):
    """Display job details and check if the user has applied"""
    job = get_object_or_404(Job, id=job_id)
    
    # Check if an Application exists for this user and job.
    existing_application = Application.objects.filter(
        applicant__user=request.user, job=job
    ).exists()

    return render(request, "job_detail.html", {
        "job": job,
        "existing_application": existing_application,
        "random": randint(1, 10000)
    })

    
@login_required
def apply_for_job(request, job_id):
    """Handles job application submission, preventing duplicate applications"""
    
    print(f"🔍 Request received to apply for job ID: {job_id}")
    
    job = get_object_or_404(Job, id=job_id)
    print(f"✅ Job found: {job.title}")

    # Get the applicant or return early with an error message
    applicant = get_object_or_404(Applicant, user=request.user)
    print(f"✅ Applicant found: {applicant.user.username}")

    # Check for existing application
    existing_application = Application.objects.filter(applicant=applicant, job=job).exists()
    print(f"🔄 Checking if applicant already applied: {existing_application}")

    if existing_application:
        print("⚠️ Applicant has already applied. Redirecting...")
        messages.error(request, "You have already applied for this job.", extra_tags="application")
        return redirect("job_detail", job_id=job.id)

    print(f"🛠 Request method: {request.method}")

    if request.method == "POST":
        print("📥 Form submission detected.")
        form = ApplicationForm(request.POST, request.FILES)

        print(f"📌 Form Data Received: {request.POST}")
        print(f"📌 Files Received: {request.FILES}")

        if form.is_valid():
            print("✅ Form is valid. Processing application...")

            raw_skill_text = form.cleaned_data.get("skills", "").strip()  # Ensure it's a string and trimmed
            print(f"🧠 Raw Skill Input: '{raw_skill_text}'")  

            # Ensure KeyBERT is extracting skills properly
            try:
                extracted_skills = extract_skills_nlp(raw_skill_text)
                if not extracted_skills:  # If KeyBERT returns empty, log it
                    print("⚠️ KeyBERT did not extract any skills.")
                    extracted_skills = raw_skill_text.split(", ")  # Fallback: Use input directly
            except Exception as e:
                print(f"❌ Error in KeyBERT extraction: {e}")
                extracted_skills = raw_skill_text.split(", ")  # Fallback in case of an error

            print(f"🔍 Extracted Skills: {extracted_skills}")  

            
            # Create and save the application
            application = form.save(commit=False)
            application.job = job
            application.applicant = applicant
            application.save()
            print("📌 Application saved.")

            # Get resume and cover letter files from form
            resume_file = form.cleaned_data.get("resume")
            cover_letter_file = form.cleaned_data.get("cover_letter")

            # Create or update candidate record
            candidate, created = Candidate.objects.get_or_create(
                user=applicant.user,
                job=job
            )

            # Update candidate fields
            if resume_file:
                candidate.resume = resume_file
            if cover_letter_file:
                candidate.cover_letter = cover_letter_file

            candidate.first_name = form.cleaned_data.get("first_name")
            candidate.last_name = form.cleaned_data.get("last_name")
            candidate.phone = form.cleaned_data.get("phone")
            candidate.address = form.cleaned_data.get("address")
            candidate.school = form.cleaned_data.get("school")
            candidate.degree = form.cleaned_data.get("degree")
            candidate.discipline = form.cleaned_data.get("discipline")
            candidate.start_date = form.cleaned_data.get("start_date")
            candidate.end_date = form.cleaned_data.get("end_date")
            candidate.linkedin_profile = form.cleaned_data.get("linkedin_profile")
            candidate.portfolio_website = form.cleaned_data.get("portfolio_website")
            candidate.how_did_you_hear = form.cleaned_data.get("how_did_you_hear")
            candidate.current_job_title = form.cleaned_data.get("current_job_title")
            candidate.current_employer = form.cleaned_data.get("current_employer")
            candidate.skills = ", ".join(extracted_skills)  # ✅ Add this line
            print("🔍 Extracted Skills Before Saving:", extracted_skills)
            candidate.application_status = "Pending"
            candidate.save()

            print(f"👤 Candidate {'created' if created else 'updated'}: {candidate}")

            # Create notifications
            if job.employer:
                EmployerNotification.objects.create(
                    employer=job.employer,
                    title="New Job Application",  
                    message=f"📩 New application received for {job.title} by {applicant.user.first_name} {applicant.user.last_name}!"
                )
                print("📢 Employer notification sent.")
            else:
                print("❌ No employer associated with this job.")

            ApplicantNotification.objects.create(
                applicant=applicant,
                title="Application Submitted",
                message=f"Your application for '{job.title}' has been submitted successfully!"
            )
            print("📢 Applicant notification sent.")

            messages.success(request, "✅ Your application has been submitted successfully!")
            print("🎉 Application process completed. Redirecting...")
            
            # If the request is AJAX, return JSON so that the JS can hide the apply button.
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            else:
                # Force the browser to recognize the change by adding a query parameter
                return redirect(f"/job/{job.id}/?applied=true")

        else:
            print("❌ Form is invalid.")
            print(f"⚠️ Form errors: {form.errors}")
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': form.errors.as_json()})
            else:
                messages.error(request, "Please fix the errors below.")
    else:
        print("📝 Rendering application form.")
        form = ApplicationForm(initial={
            'first_name': applicant.user.first_name,
            'last_name': applicant.user.last_name,
            'email': applicant.user.email,
            'phone': getattr(applicant, 'phone', ''),
            'address': getattr(applicant, 'address', ''),
            'school': getattr(applicant, 'school', ''),
            'degree': getattr(applicant, 'degree', ''),
            'discipline': getattr(applicant, 'discipline', ''),
            'start_date': getattr(applicant, 'start_date', ''),
            'end_date': getattr(applicant, 'end_date', ''),
            'linkedin_profile': getattr(applicant, 'linkedin_profile', ''),
            'portfolio_website': getattr(applicant, 'portfolio_website', ''),
            'current_job_title': getattr(applicant, 'current_job_title', ''),
            'current_employer': getattr(applicant, 'current_employer', ''),
            'skills': getattr(applicant, 'skills', ''),
        })
    

    return render(request, "applicants_application.html", {
        "form": form,
        "job": job,
        "existing_application": Application.objects.filter(applicant=applicant, job=job).exists()
    })


@applicant_only
@login_required
def applicants_notifications(request):
    """Display real notifications for the logged-in applicant"""
    applicant = get_object_or_404(Applicant, user=request.user)
    notifications = ApplicantNotification.objects.filter(applicant=applicant).order_by('-timestamp')

    return render(request, 'applicants_notifications.html', {'notifications': notifications})

@applicant_only
@login_required
def applicants_application(request, job_id):
    """
    Displays the job application form and processes the submission.
    """
    job = get_object_or_404(Job, id=job_id)
    applicant = get_object_or_404(Applicant, user=request.user)
    
    # If an application already exists, redirect to the job detail page.
    if Application.objects.filter(applicant=applicant, job=job).exists():
        messages.warning(request, "You have already applied for this job.")
        return redirect('job_detail', job_id=job.id)

    if request.method == "POST":
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            # Save form with commit=False so we can attach job and applicant
            application = form.save(commit=False)
            application.job = job
            application.applicant = applicant
            application.save()

            # Optionally, update or create candidate record here...
            candidate, created = Candidate.objects.get_or_create(
                user=applicant.user, job=job
            )
            candidate.resume = form.cleaned_data.get("resume")
            candidate.cover_letter = form.cleaned_data.get("cover_letter")
            candidate.application_status = "Pending"
            candidate.save()

            # Notifications
            if job.employer:
                EmployerNotification.objects.create(
                    employer=job.employer,
                    title="New Job Application",
                    message=f"New application for {job.title} by {applicant.user.username}"
                )
            ApplicantNotification.objects.create(
                applicant=applicant,
                title="Application Submitted",
                message=f"Your application for '{job.title}' has been submitted successfully!"
            )

            messages.success(request, "Your application has been submitted successfully!")
            return redirect('job_detail', job_id=job.id)
        else:
            messages.error(request, "Please fix the errors in your application form.")
    else:
        form = ApplicationForm()

    return render(request, 'applicants_application.html', {
        'form': form,
        'job': job,
    })

@applicant_only
@login_required
def applicants_analytics(request):
    """ Fetch and display real applicant analytics data """

    # Get the logged-in applicant
    applicant = request.user.applicant

    # Fetch statistics
    total_applications = Application.objects.filter(applicant=applicant).count()
    candidates = Candidate.objects.filter(user=request.user)
    # Only count interviews if the user actually has applications
    applications = Application.objects.filter(applicant=applicant)
    if applications.exists():
        applied_jobs = applications.values_list('job', flat=True)
        candidates = Candidate.objects.filter(user=request.user, job__in=applied_jobs)
        interviews_scheduled = Interview.objects.filter(candidate__in=candidates).count()
    else:
        interviews_scheduled = 0
    job_offers_received = Application.objects.filter(applicant=applicant, status="hired").count()
    
    # Calculate acceptance rate
    accepted_offers = Application.objects.filter(applicant=applicant, status="hired", confirm_information=True).count()
    offer_acceptance_rate = (accepted_offers / job_offers_received * 100) if job_offers_received > 0 else 0

    # Applications over time (grouping by month)
    applications_per_month = Application.objects.filter(applicant=applicant).values_list("applied_at", flat=True)
    
    month_counts = {m: 0 for m in ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]}  # Adjust based on data range
    for date in applications_per_month:
        month_name = date.strftime("%b")
        if month_name in month_counts:
            month_counts[month_name] += 1

    # Offer Acceptance Breakdown
    accepted_count = accepted_offers
    declined_count = job_offers_received - accepted_offers

    # Fetch applications list for table
    applications = Application.objects.filter(applicant=applicant).select_related("job")

    interviews = Interview.objects.filter(candidate__user=request.user)

    return render(request, 'applicants_analytics.html', {
        "total_applications": total_applications,
        "interviews_scheduled": interviews_scheduled,
        "job_offers_received": job_offers_received,
        "offer_acceptance_rate": round(offer_acceptance_rate, 2),
        "applications": applications,  # Pass applications for the table
        "applications_over_time": json.dumps(list(month_counts.values())),
        "offer_acceptance_breakdown": json.dumps([accepted_count, declined_count]),
    })