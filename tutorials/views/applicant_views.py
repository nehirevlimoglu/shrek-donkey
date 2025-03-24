from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages  # Import the messages module
from tutorials.models.applicants_models import Applicant, Application, ApplicantNotification
from tutorials.forms.applicants_forms import ApplicantForm, ApplicationForm
from django.contrib.auth.decorators import login_required
from tutorials.decorators import applicant_only  # Import the decorator
from tutorials.models.employer_models import Job, EmployerNotification, JobTitle, Candidate, WorkExperience
from django.contrib.messages import get_messages
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from tutorials.utils import extract_skills_nlp
from random import randint
import json
from datetime import date
from tutorials.models.employer_models import Interview
from tutorials.utils import match_candidates_to_job
from django.http import HttpResponseForbidden


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
    applicant = get_object_or_404(Applicant, user=request.user)
    applied_jobs = Application.objects.filter(applicant=applicant).select_related('job')

    return render(request, 'applicants_applied_jobs.html', {
        'applied_jobs': applied_jobs,
    })


@login_required
def applicants_favourites(request):
    try:
        applicant = Applicant.objects.get(user=request.user)
    except Applicant.DoesNotExist:
        return HttpResponseForbidden("You are not authorized to view this page.")

    favorite_jobs = applicant.favorites.all()
    return render(request, 'applicants_favourites.html', {'favorite_jobs': favorite_jobs})

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


# ------------------------------------------------------------------------------
# APPLY_FOR_JOB VIEW - MODIFIED TO SAVE EDUCATION DATA INTO Application.education
# ------------------------------------------------------------------------------
@login_required
def apply_for_job(request, job_id):
    """Handles job application submission, preventing duplicate applications"""
    
    print(f"🔍 Request received to apply for job ID: {job_id}")
    job = get_object_or_404(Job, id=job_id)
    print(f"✅ Job found: {job.title}")

    # Get the applicant
    applicant = get_object_or_404(Applicant, user=request.user)
    print(f"✅ Applicant found: {applicant.user.username}")

    # Check for an existing application
    if Application.objects.filter(applicant=applicant, job=job).exists():
        print("⚠️ Applicant has already applied. Redirecting...")
        messages.error(request, "You have already applied for this job.", extra_tags="application")
        return redirect("job_detail", job_id=job.id)

    if request.method == "POST":
        print("📥 Form submission detected.")
        form = ApplicationForm(request.POST, request.FILES)
        print(f"📌 Form Data Received: {request.POST}")
        print(f"📌 Files Received: {request.FILES}")

        if form.is_valid():
            print("✅ Form is valid. Processing application...")

            # Extract skills (existing code)
            raw_skill_text = form.cleaned_data.get("skills", "").strip()
            print(f"🧠 Raw Skill Input: '{raw_skill_text}'")
            try:
                extracted_skills = extract_skills_nlp(raw_skill_text)
                if not extracted_skills:
                    print("⚠️ KeyBERT did not extract any skills.")
                    extracted_skills = raw_skill_text.split(", ")
            except Exception as e:
                print(f"❌ Error in KeyBERT extraction: {e}")
                extracted_skills = raw_skill_text.split(", ")
            print(f"🔍 Extracted Skills: {extracted_skills}")

            # Create the Application object without saving yet
            application = form.save(commit=False)
            application.job = job
            application.applicant = applicant

            # -----------------------------
            # Parse dynamic education fields
            # -----------------------------
            schools = request.POST.getlist('school[]')
            degrees = request.POST.getlist('degree[]')
            disciplines = request.POST.getlist('discipline[]')
            start_dates = request.POST.getlist('start_date[]')
            end_dates = request.POST.getlist('end_date[]')

            education_data = []
            for i in range(len(schools)):
                education_data.append({
                    "school": schools[i],
                    "degree": degrees[i],
                    "discipline": disciplines[i],
                    "start_date": start_dates[i],
                    "end_date": end_dates[i]
                })
            application.education = education_data
            application.save()  # Save education data
            print("📌 Application saved with dynamic education entries.")

            # -----------------------------
            # Parse dynamic work experience fields
            # -----------------------------
            work_job_titles = request.POST.getlist('work_job_title[]')
            work_employers = request.POST.getlist('work_employer[]')
            work_start_dates = request.POST.getlist('work_start_date[]')
            work_end_dates = request.POST.getlist('work_end_date[]')
            job_descriptions = request.POST.getlist('job_description[]')

            work_experience_data = []
            for i in range(len(work_job_titles)):
                work_experience_data.append({
                    "work_job_title": work_job_titles[i],
                    "work_employer": work_employers[i],
                    "work_start_date": work_start_dates[i],
                    "work_end_date": work_end_dates[i],
                    "job_description": job_descriptions[i],
                })
            application.work_experience = work_experience_data
            application.save()  # Save work experience data as JSON in Application
            print("📌 Application saved with dynamic work experience entries.")

            # -----------------------------
            # Parse dynamic work experience fields
            # -----------------------------
            work_job_titles = request.POST.getlist('work_job_title[]')
            work_employers = request.POST.getlist('work_employer[]')
            work_start_dates = request.POST.getlist('work_start_date[]')
            work_end_dates = request.POST.getlist('work_end_date[]')
            job_descriptions = request.POST.getlist('job_description[]')

            work_experience_data = []
            for i in range(len(work_job_titles)):
                work_experience_data.append({
                    "work_job_title": work_job_titles[i],
                    "work_employer": work_employers[i],
                    "work_start_date": work_start_dates[i],
                    "work_end_date": work_end_dates[i],
                    "job_description": job_descriptions[i],
                })
            application.work_experience = work_experience_data
            application.save()  # Save work experience data as JSON in Application
            print("📌 Application saved with dynamic work experience entries.")

            # -----------------------------
            # Update or create candidate record
            # -----------------------------
            candidate, created = Candidate.objects.get_or_create(
                user=applicant.user,
                job=job
            )
            resume_file = form.cleaned_data.get("resume")
            cover_letter_file = form.cleaned_data.get("cover_letter")
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
            candidate.skills = ", ".join(extracted_skills)
            candidate.application_status = "Pending"
            candidate.save()
            print(f"👤 Candidate {'created' if created else 'updated'}: {candidate}")

            # -----------------------------
            # Create WorkExperience model objects for the candidate
            # -----------------------------
            # Make sure to import your WorkExperience model at the top:
            # from tutorials.models.employer_models import WorkExperience

            # Optionally, clear out old entries for this candidate if you want to refresh them
            candidate.work_experiences.all().delete()

            for work in work_experience_data:
                if work.get("work_job_title") and work.get("work_start_date"):
                    WorkExperience.objects.create(
                        candidate=candidate,
                        job_title=work.get("work_job_title"),
                        employer=work.get("work_employer"),
                        start_date=work.get("work_start_date"),  # Ensure proper date format or parse it
                        end_date=work.get("work_end_date") or None,
                        job_description=work.get("job_description")
                    )
                    print(f"📌 Work experience added: {work.get('work_job_title')} at {work.get('work_employer')}")
                else:
                    print("⚠️ Incomplete work experience entry; skipping.")


            # -----------------------------
            # Notifications
            # -----------------------------
            matched_candidates = match_candidates_to_job(job.title, top_n=10)  # get top 10 matches
            print("DEBUG: Matched candidates list:", matched_candidates)

            if isinstance(matched_candidates, list):
                for cand, score in matched_candidates:
                    print(f"DEBUG: Candidate {cand.user.username} with ID {cand.id} has score {score:.2f}")
                    if cand.id == candidate.id and score >= 0.68:
                        EmployerNotification.objects.create(
                            employer=job.employer,
                            title="New Matched Candidate Found",
                            message=(f"Your job '{job.title}' just received a matched candidate: "
                                    f"{candidate.user.username} (Score: {score:.2f}).")
                        )
                        print("📢 Matched candidate notification sent to employer via match_candidates_to_job().")
                        break  # No need to check further
            else:
                print(f"⚠️ Matching system returned a message instead of a list: {matched_candidates}")



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
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            else:
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


# ------------------------------------------------------------------------------
# APPLICANTS_APPLICATION VIEW - ALSO MODIFIED TO SAVE EDUCATION INTO JSON
# ------------------------------------------------------------------------------
@applicant_only
@login_required
def applicants_application(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    applicant = get_object_or_404(Applicant, user=request.user)

    if Application.objects.filter(applicant=applicant, job=job).exists():
        messages.warning(request, "You have already applied for this job.")
        return redirect('job_detail', job_id=job.id)

    if request.method == "POST":
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.applicant = applicant

            # 1) Parse education
            schools = request.POST.getlist('school[]')
            degrees = request.POST.getlist('degree[]')
            disciplines = request.POST.getlist('discipline[]')
            start_dates = request.POST.getlist('start_date[]')
            end_dates = request.POST.getlist('end_date[]')

            education_data = []
            for i in range(len(schools)):
                education_data.append({
                    "school": schools[i],
                    "degree": degrees[i],
                    "discipline": disciplines[i],
                    "start_date": start_dates[i],
                    "end_date": end_dates[i]
                })
            application.education = education_data
            application.save()

            # 2) Parse work experience
            work_job_titles = request.POST.getlist('work_job_title[]')
            work_employers = request.POST.getlist('work_employer[]')
            work_start_dates = request.POST.getlist('work_start_date[]')
            work_end_dates = request.POST.getlist('work_end_date[]')
            job_descriptions = request.POST.getlist('job_description[]')

            work_experience_data = []
            for i in range(len(work_job_titles)):
                work_experience_data.append({
                    "work_job_title": work_job_titles[i],
                    "work_employer": work_employers[i],
                    "work_start_date": work_start_dates[i],
                    "work_end_date": work_end_dates[i],
                    "job_description": job_descriptions[i],
                })
            application.work_experience = work_experience_data
            application.save()

            # (Optional) Create/update Candidate, send notifications, etc.
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
    applicant = request.user.applicant

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

    # Just count all hired applications as accepted
    accepted_offers = Application.objects.filter(applicant=applicant, status="hired").count()
    declined_offers = Application.objects.filter(applicant=applicant, status="rejected").count()

    total_offers = accepted_offers + declined_offers
    offer_acceptance_rate = (accepted_offers / total_offers * 100) if total_offers > 0 else 0

    accepted_count = accepted_offers
    declined_count = declined_offers

    applications = Application.objects.filter(applicant=applicant).select_related("job")

    interviews = Interview.objects.filter(candidate__user=request.user)

    # Dynamically build the pie chart data
    offer_labels = []
    offer_data = []
    offer_colors = []

    # Always push Accepted first, then Declined — even if their count is zero
    offer_labels = ["Accepted", "Declined"]
    offer_data = [accepted_offers, declined_offers]
    offer_colors = ["#34A853", "#EA4335"]

    return render(request, 'applicants_analytics.html', {
        "total_applications": total_applications,
        "interviews_scheduled": interviews_scheduled,
        "job_offers_received": job_offers_received,
        "offer_acceptance_rate": round(offer_acceptance_rate, 2),
        "applications": applications,
        "offer_chart_labels": offer_labels,
        "offer_chart_data": offer_data,
        "offer_chart_colors": offer_colors,
    })

from django.views.decorators.http import require_POST

@login_required
@csrf_exempt  # Ensure CSRF is handled appropriately (alternatively, include CSRF token in your JS)
@require_POST
def toggle_favorite(request):
    data = json.loads(request.body)
    job_id = data.get('job_id')
    # Assuming you have a Job model and the applicant profile is attached to the user
    try:
        job = Job.objects.get(id=job_id)
        applicant = request.user.applicant  # Make sure the user has an applicant profile
    except Job.DoesNotExist:
        return JsonResponse({'error': 'Job not found'}, status=404)

    if job in applicant.favorites.all():
        applicant.favorites.remove(job)
        favorited = False
    else:
        applicant.favorites.add(job)
        favorited = True
    # Ensure that the change is saved (ManyToManyFields usually update immediately)
    return JsonResponse({'favorited': favorited})