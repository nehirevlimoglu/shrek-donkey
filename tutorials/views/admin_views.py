from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from tutorials.models.admin_models import Admin
from tutorials.models.admin_models import Notification
from django.http import JsonResponse, HttpResponse
from tutorials.models.user_model import User
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
import json
from tutorials.models.employer_models import Job, Candidate, Employer
from django.views.decorators.http import require_POST

def is_admin(user):
    return user.role == 'Admin'

@user_passes_test(is_admin)
def admin_home_page(request):
    admins = Admin.objects.all()  # Your existing data
    
    # Get total number of active users
    total_active_users = User.objects.filter(is_active=True).count()
    
    return render(request, 'admin_home_page.html', {
        'admins': admins,
        'total_active_users': total_active_users,
    })


@user_passes_test(is_admin)
def admin_job_listings(request):
    # Get all job listings, ordered by creation date (newest first)
    jobs = Job.objects.all().order_by('-created_at')
    
    # Add applicant count information for each job
    for job in jobs:
        job.applicant_count = Candidate.objects.filter(job=job).count()
        
        # Determine job status based on application deadline
        if job.application_deadline:
            if job.application_deadline < timezone.now().date():
                job.status = "Closed"
            else:
                job.status = "Open"
        else:
            job.status = "Open"
    
    return render(request, 'admin_job_listings.html', {
        'jobs': jobs,
    })

def admin_settings(request):
    return render(request, 'admin_settings.html')

@user_passes_test(is_admin)
def admin_notifications(request):
    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')

    notifications.update(is_read=True)

    return render(request, 'admin_notifications.html', {
        'notifications': notifications,
        'unread_count': unread_count, 
    })

@user_passes_test(is_admin)
def get_active_users_data(request):
    period = request.GET.get('period', 'day')
    
    today = timezone.now().date()
    
    if period == 'day':
        # Get data for the past 7 days
        days = []
        values = []
        
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            next_day = day + timedelta(days=1)
            
            # Calculate active users for the day (based on last login time)
            count = User.objects.filter(
                last_login__gte=day,
                last_login__lt=next_day
            ).count()
            
            days.append(day.strftime('%a'))  # Abbreviated weekday name
            values.append(count)
        
        return JsonResponse({
            'labels': days,
            'values': values
        })
        
    elif period == 'week':
        # Get data for the past 4 weeks
        weeks = []
        values = []
        
        for i in range(3, -1, -1):
            week_start = today - timedelta(days=today.weekday() + 7 * i)
            week_end = week_start + timedelta(days=7)
            
            # Calculate active users for the week
            count = User.objects.filter(
                last_login__gte=week_start,
                last_login__lt=week_end
            ).count()
            
            weeks.append(f'Week {i+1}')
            values.append(count)
        
        return JsonResponse({
            'labels': weeks,
            'values': values
        })
        
    elif period == 'month':
        # Get data for the past 12 months
        months = []
        values = []
        
        for i in range(11, -1, -1):
            # Calculate month
            month_date = today.replace(day=1) - timedelta(days=1)
            month_date = month_date.replace(day=1)
            month_date = month_date.replace(month=((today.month - i - 1) % 12) + 1)
            if today.month - i <= 0:
                month_date = month_date.replace(year=today.year - 1)
            
            next_month = month_date.replace(month=month_date.month % 12 + 1)
            if month_date.month == 12:
                next_month = next_month.replace(year=month_date.year + 1)
            
            # Calculate active users for the month
            count = User.objects.filter(
                last_login__gte=month_date,
                last_login__lt=next_month
            ).count()
            
            months.append(month_date.strftime('%b'))  # Abbreviated month name
            values.append(count)
        
        return JsonResponse({
            'labels': months,
            'values': values
        })
    
    return JsonResponse({'error': 'Invalid period'}, status=400)

@user_passes_test(is_admin)
def admin_job_detail(request, job_id):

    job = get_object_or_404(Job, id=job_id)
    

    candidates = Candidate.objects.filter(job=job).select_related('user')

    employer = job.employer
    

    if job.application_deadline:
        if job.application_deadline < timezone.now().date():
            job.status = "Closed"
        else:
            job.status = "Open"
    else:
        job.status = "Open"
    
    return render(request, 'admin_job_detail.html', {
        'job': job,
        'candidates': candidates,
        'employer': employer,
        'candidate_count': candidates.count(),
    })

@user_passes_test(is_admin)
def admin_edit_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    
    if request.method == 'POST':
        # Update job information
        job.title = request.POST.get('title')
        job.company_name = request.POST.get('company_name')
        job.location = request.POST.get('location')
        job.job_type = request.POST.get('job_type')
        
        salary = request.POST.get('salary')
        if salary:
            job.salary = salary
        
        job.description = request.POST.get('description')
        job.requirements = request.POST.get('requirements')
        job.benefits = request.POST.get('benefits')
        
        deadline = request.POST.get('application_deadline')
        if deadline:
            job.application_deadline = deadline
        
        job.contact_email = request.POST.get('contact_email')
        
        job.save()
        
        return redirect('admin_job_detail', job_id=job.id)
    
    return render(request, 'admin_edit_job.html', {
        'job': job,
    })

@user_passes_test(is_admin)
@require_POST
def admin_delete_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    job.delete()
    return JsonResponse({'status': 'success'})

@user_passes_test(is_admin)
@require_POST
def admin_toggle_job_status(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    
    data = json.loads(request.body)
    status = data.get('status')
    
    if status == 'Closed':
        # Set deadline to current date to indicate job is closed
        job.application_deadline = timezone.now().date()
    elif status == 'Open':
        # Set deadline to a future date to indicate job is open
        job.application_deadline = timezone.now().date() + timedelta(days=30)
    
    job.save()
    
    return JsonResponse({'status': 'success'})

