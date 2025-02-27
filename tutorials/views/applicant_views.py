from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from tutorials.models.applicants_models import Applicant, FavoriteJob, Application
from tutorials.forms.applicants_forms import ApplicantForm
from django.contrib.auth.decorators import login_required
from decorators import applicant_only  # Import the decorator
from tutorials.models.employer_models import Job
from django.http import JsonResponse
from django.views.decorators.http import require_POST

@login_required
def applicants_home_page(request):
    # Get all real jobs from the database
    jobs = Job.objects.all().order_by('-created_at')
    
    # Get user's favorites and applications
    favorited_jobs = FavoriteJob.objects.filter(user=request.user)
    applied_jobs = Application.objects.filter(user=request.user)
    
    # Get the IDs for template checks
    favorited_job_ids = favorited_jobs.values_list('job_id', flat=True)
    applied_job_ids = applied_jobs.values_list('job_id', flat=True)
    
    # Get accurate counts
    total_jobs = jobs.count()  # Only real jobs from database
    favorite_count = favorited_jobs.count()
    applications_sent = applied_jobs.count()
    
    return render(request, 'applicants_home_page.html', {
        'jobs': jobs,
        'favorited_jobs': favorited_job_ids,
        'applied_jobs': applied_job_ids,
        'total_jobs': total_jobs,
        'favorite_count': favorite_count,
        'applications_sent': applications_sent
    })

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
    applied_jobs = Application.objects.filter(user=request.user).select_related('job')
    return render(request, 'applicants_applied_jobs.html', {
        'applied_jobs': applied_jobs,
    })

@applicant_only
def applicants_favourites(request):
    favorite_jobs = FavoriteJob.objects.filter(user=request.user).select_related('job')
    return render(request, 'applicants_favourites.html', {
        'favorite_jobs': favorite_jobs,
        'favorited_jobs': [fav.job.id for fav in favorite_jobs]  # For checking active state
    })

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

@require_POST
@login_required
def toggle_favorite(request, job_id):
    try:
        job = get_object_or_404(Job, id=job_id)
        favorite, created = FavoriteJob.objects.get_or_create(user=request.user, job=job)
        
        if not created:  # If it existed, delete it (unfavorite)
            favorite.delete()
            return JsonResponse({'status': 'removed'})
            
        return JsonResponse({'status': 'added'})
    except Job.DoesNotExist:
        return JsonResponse({'error': 'Job not found'}, status=404)

@require_POST
@login_required
def apply_for_job(request, job_id):
    try:
        job = get_object_or_404(Job, id=job_id)
        application, created = Application.objects.get_or_create(
            job=job,
            user=request.user,
            defaults={'status': 'applied'}
        )
        
        if created:
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'already_applied'})
    except Job.DoesNotExist:
        return JsonResponse({'error': 'Job not found'}, status=404)
