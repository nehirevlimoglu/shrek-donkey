from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import user_passes_test
from tutorials.models.admin_models import Admin
from tutorials.models.admin_models import Notification, NotificationPreference
from tutorials.models.employer_models import EmployerNotification
from django.http import JsonResponse, HttpResponse
from tutorials.models.user_model import User
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
import json
from tutorials.models.employer_models import Job, Candidate, Employer
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages

def is_admin(user):
    return user.role == 'Admin'


@user_passes_test(is_admin)
def admin_home_page(request):
    admins = Admin.objects.all()  # Your existing data
    
    total_job_listings = Job.objects.count()
    
    pending_applications = Candidate.objects.filter(application_status='Pending').count()
    
    last_week = timezone.now() - timedelta(days=7)
    total_active_users = User.objects.filter(last_login__gte=last_week).count()
    
    current_month = timezone.now().month
    current_year = timezone.now().year
    new_hires_this_month = Candidate.objects.filter(
        application_status='Hired',
        application_date__month=current_month,
        application_date__year=current_year
    ).count()
    
    return render(request, 'admin_home_page.html', {
        'admins': admins,
        'total_job_listings': total_job_listings,
        'pending_applications': pending_applications,
        'total_active_users': total_active_users,
        'new_hires_this_month': new_hires_this_month,
    })


@user_passes_test(is_admin)
def admin_job_listings(request):
    # Get search parameters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', 'all')
    
    # Base query
    jobs_query = Job.objects.all()
    
    # Apply search filter
    if search_query:
        jobs_query = jobs_query.filter(
            Q(title__icontains=search_query) | 
            Q(company_name__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    # Apply status filter
    if status_filter != 'all':
        today = timezone.now().date()
        if status_filter == 'open':
            # Open jobs: no deadline or deadline after today
            jobs_query = jobs_query.filter(
                Q(application_deadline__isnull=True) | 
                Q(application_deadline__gt=today)
            )
        elif status_filter == 'closed':
            # Closed jobs: deadline before today
            jobs_query = jobs_query.filter(application_deadline__lte=today)
    
    # Order by creation date (newest first)
    jobs_query = jobs_query.order_by('-created_at')
    
    # Get statistics
    total_jobs = Job.objects.count()
    open_jobs = Job.objects.filter(
        Q(application_deadline__isnull=True) | 
        Q(application_deadline__gt=timezone.now().date())
    ).count()
    closed_jobs = total_jobs - open_jobs
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(jobs_query, 5)  # Show 5 jobs per page instead of 10
    
    try:
        jobs_page = paginator.page(page)
    except PageNotAnInteger:
        jobs_page = paginator.page(1)
    except EmptyPage:
        jobs_page = paginator.page(paginator.num_pages)
    
    # Add applicant count and status information
    for job in jobs_page:
        job.applicant_count = Candidate.objects.filter(job=job).count()
        
        # Determine job status
        if job.application_deadline:
            if job.application_deadline < timezone.now().date():
                job.status = "Closed"
            else:
                job.status = "Open"
        else:
            job.status = "Open"
    
    return render(request, 'admin_job_listings.html', {
        'jobs': jobs_page,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_jobs': total_jobs,
        'open_jobs': open_jobs,
        'closed_jobs': closed_jobs,
    })

@user_passes_test(is_admin)
def admin_settings(request):
    # Get the currently logged in admin user
    user = request.user
    try:
        admin = Admin.objects.get(id=user.id)
    except Admin.DoesNotExist:
        admin = None
    
    # Get the tab parameter, default to 'profile'
    tab = request.GET.get('tab', 'profile')
    
    error = None
    
    # Handle profile update
    if request.method == 'POST' and 'update_profile' in request.POST:
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone_number = request.POST.get('phone_number')
        
        # Check if the username already exists (excluding the current user)
        if User.objects.filter(username=username).exclude(id=user.id).exists():
            error = "Username already exists. Please choose a different one."
        else:
            # Update the user profile
            user.username = username
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            
            # Update admin-specific fields
            if admin:
                admin.phone_number = phone_number
                admin.save()
            
            messages.success(request, "Profile updated successfully.")
            return redirect('admin_settings')
    
    # Handle password change
    elif request.method == 'POST' and 'change_password' in request.POST:
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Check if current password is correct
        if not user.check_password(current_password):
            error = "Current password is incorrect."
            tab = 'password'
        elif new_password != confirm_password:
            error = "New passwords do not match."
            tab = 'password'
        elif len(new_password) < 8:
            error = "Password must be at least 8 characters long."
            tab = 'password'
        else:
            # Set the new password
            user.set_password(new_password)
            user.save()
            
            # Update the session to prevent the user from being logged out
            update_session_auth_hash(request, user)
            
            messages.success(request, "Password changed successfully.")
            return redirect('admin_settings')
    
    # Handle notification preferences update
    elif request.method == 'POST' and 'update_notification_prefs' in request.POST:
        # Get notification preferences
        job_notifications = 'job_notifications' in request.POST
        application_notifications = 'application_notifications' in request.POST
        user_notifications = 'user_notifications' in request.POST
        system_notifications = 'system_notifications' in request.POST
        
        # Get delivery methods
        email_delivery = 'email_delivery' in request.POST
        dashboard_delivery = 'dashboard_delivery' in request.POST
        
        # Save notification preferences to admin user
        if admin:
            # Get or create notification preferences
            notification_prefs, created = NotificationPreference.objects.get_or_create(admin=admin)
            
            # Update the preferences
            notification_prefs.job_notifications = job_notifications
            notification_prefs.application_notifications = application_notifications
            notification_prefs.user_notifications = user_notifications
            notification_prefs.system_notifications = system_notifications
            notification_prefs.email_delivery = email_delivery
            notification_prefs.dashboard_delivery = dashboard_delivery
            notification_prefs.save()
            
            messages.success(request, "Notification preferences updated successfully.")
            return redirect('admin_settings')
    
    # Get notification preferences from database or use defaults
    notification_prefs = None
    if admin:
        try:
            notification_prefs = NotificationPreference.objects.get(admin=admin)
        except NotificationPreference.DoesNotExist:
            # Use default values
            notification_prefs = {
                'job_notifications': True,
                'application_notifications': True,
                'user_notifications': True,
                'system_notifications': True,
                'email_delivery': True,
                'dashboard_delivery': True
            }
    else:
        # Use default values
        notification_prefs = {
            'job_notifications': True,
            'application_notifications': True,
            'user_notifications': True,
            'system_notifications': True,
            'email_delivery': True,
            'dashboard_delivery': True
        }
    
    context = {
        'tab': tab,
        'admin': admin,
        'user': user,
        'error': error,
        'notification_prefs': notification_prefs
    }
    
    return render(request, 'admin_settings.html', context)


@user_passes_test(is_admin)
def admin_notifications(request):
    # Get query parameters
    notification_type = request.GET.get('type', 'all')
    priority = request.GET.get('priority', 'all')
    is_read = request.GET.get('is_read', 'all')
    search_query = request.GET.get('search', '')
    page = request.GET.get('page', 1)
    
    # Base queryset
    notifications = Notification.objects.filter(is_deleted=False)
    
    # Apply filters
    if notification_type != 'all':
        notifications = notifications.filter(notification_type=notification_type)
    
    if priority != 'all':
        notifications = notifications.filter(priority=priority)
    
    if is_read == 'unread':
        notifications = notifications.filter(is_read=False)
    elif is_read == 'read':
        notifications = notifications.filter(is_read=True)
    
    if search_query:
        notifications = notifications.filter(
            Q(title__icontains=search_query) | 
            Q(message__icontains=search_query)
        )
    
    # Count totals for statistics
    total_count = notifications.count()
    unread_count = notifications.filter(is_read=False).count()
    feedback_count = notifications.filter(notification_type='feedback').count()
    
    # Get counts by type and priority for filter display
    type_counts = {
        'general': notifications.filter(notification_type='general').count(),
        'job': notifications.filter(notification_type='job').count(),
        'application': notifications.filter(notification_type='application').count(),
        'user': notifications.filter(notification_type='user').count(),
        'system': notifications.filter(notification_type='system').count(),
        'feedback': notifications.filter(notification_type='feedback').count(),
    }
    
    priority_counts = {
        'high': notifications.filter(priority='high').count(),
        'medium': notifications.filter(priority='medium').count(),
        'low': notifications.filter(priority='low').count(),
    }
    
    # Paginate notifications
    paginator = Paginator(notifications, 10)  # Show 10 notifications per page
    try:
        notifications = paginator.page(page)
    except PageNotAnInteger:
        notifications = paginator.page(1)
    except EmptyPage:
        notifications = paginator.page(paginator.num_pages)
    
    context = {
        'notifications': notifications,
        'notification_type': notification_type,
        'priority': priority,
        'is_read': is_read,
        'search_query': search_query,
        'total_count': total_count,
        'unread_count': unread_count,
        'feedback_count': feedback_count,
        'type_counts': type_counts,
        'priority_counts': priority_counts,
    }
    
    return render(request, 'admin_notifications.html', context)

@user_passes_test(is_admin)
def admin_notifications_count(request):
    """Return the count of all unread notifications for admin dashboard"""
    # Count all unread and not deleted notifications, not just the current user's
    unread_count = Notification.objects.filter(is_read=False, is_deleted=False).count()
    return JsonResponse({'count': unread_count})

@user_passes_test(is_admin)
@require_POST
def mark_notification_as_read(request, notification_id):
    """Mark a single notification as read"""
    notification = get_object_or_404(Notification, id=notification_id)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'success'})

@user_passes_test(is_admin)
@require_POST
def mark_all_notifications_as_read(request):
    """Mark all notifications as read"""
    Notification.objects.filter(is_read=False).update(is_read=True)
    return JsonResponse({'status': 'success'})

@user_passes_test(is_admin)
@require_POST
def delete_notification(request, notification_id):
    """Soft delete a notification (mark as deleted)"""
    notification = get_object_or_404(Notification, id=notification_id)
    notification.is_deleted = True
    notification.save()
    return JsonResponse({'status': 'success'})

@user_passes_test(is_admin)
@require_POST
def delete_all_notifications(request):
    """Soft delete all notifications"""
    Notification.objects.all().update(is_deleted=True)
    return JsonResponse({'status': 'success'})

@user_passes_test(is_admin)
def generate_admin_notification(request):
    """Generate a test notification for the admin user"""
    Notification.objects.create(
        recipient=request.user,
        title="Test Notification",
        message="This is a test notification for admin users.",
        notification_type='general',
        priority='medium',
        is_read=False
    )
    return redirect('admin_notifications')

@user_passes_test(is_admin)
def generate_test_notifications(request):
    """Generate multiple test notifications for demonstration purposes"""
    # Create different types of notifications with different priorities
    notification_types = ['general', 'job', 'application', 'user', 'system', 'feedback']
    priorities = ['high', 'medium', 'low']
    
    # Create one of each type
    for notification_type in notification_types:
        for priority in priorities:
            Notification.objects.create(
                recipient=request.user,
                title=f"Test {notification_type.title()} Notification",
                message=f"This is a test {notification_type} notification with {priority} priority.",
                notification_type=notification_type,
                priority=priority,
                is_read=False
            )
    
    # Add specific feedback notifications with different feedback types
    feedback_types = ['suggestion', 'bug_report', 'compliment', 'complaint', 'other']
    for feedback_type in feedback_types:
        Notification.objects.create(
            recipient=request.user,
            title=f"Test Feedback: {feedback_type.replace('_', ' ').title()}",
            message=f"This is a test feedback of type {feedback_type.replace('_', ' ')}.",
            notification_type='feedback',
            priority='medium',
            is_read=False,
            feedback_type=feedback_type,
            sender_type='applicant'
        )
    
    return redirect('admin_notifications')

def create_admin_notification(user, title, message, notification_type='general', priority='medium', related_object_id=None, related_object_type=None, action_url=None):
    """
    Enhanced utility function to create notifications for admin users
    
    Args:
        user: The recipient user (should be an admin)
        title: The notification title
        message: The notification message content
        notification_type: Type of notification (job, application, user, system, general)
        priority: Priority level (high, medium, low)
        related_object_id: ID of related object (e.g., job ID, user ID)
        related_object_type: Type of related object (e.g., 'job', 'application')
        action_url: URL for action button in notification
    """
    if user.role == 'Admin':
        Notification.objects.create(
            recipient=user,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            related_object_id=related_object_id,
            related_object_type=related_object_type,
            action_url=action_url,
            is_read=False
        )

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

@user_passes_test(is_admin)
def admin_applications_view(request):
    # Get search parameters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', 'all')
    
    # Base query
    applications_query = Candidate.objects.all().select_related('user', 'job')
    
    # Apply search filter
    if search_query:
        applications_query = applications_query.filter(
            Q(user__username__icontains=search_query) | 
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(job__title__icontains=search_query) |
            Q(job__company_name__icontains=search_query)
        )
    
    # Apply status filter
    if status_filter != 'all':
        applications_query = applications_query.filter(application_status=status_filter)
    
    # Order by application date (newest first)
    applications_query = applications_query.order_by('-application_date')
    
    # Get statistics
    total_applications = Candidate.objects.count()
    pending_applications = Candidate.objects.filter(application_status='Pending').count()
    interview_applications = Candidate.objects.filter(application_status='Interview').count()
    hired_applications = Candidate.objects.filter(application_status='Hired').count()
    rejected_applications = Candidate.objects.filter(application_status='Rejected').count()
    
    # Pagination - show 5 applications per page for better pagination testing
    page = request.GET.get('page', 1)
    paginator = Paginator(applications_query, 5)  # Show 5 applications per page
    
    try:
        applications_page = paginator.page(page)
    except PageNotAnInteger:
        applications_page = paginator.page(1)
    except EmptyPage:
        applications_page = paginator.page(paginator.num_pages)
    
    return render(request, 'admin_applications_view.html', {
        'applications': applications_page,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'interview_applications': interview_applications,
        'hired_applications': hired_applications,
        'rejected_applications': rejected_applications,
    })


import logging
logger = logging.getLogger(__name__)


@csrf_exempt
def update_job_status(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            job_id = data.get("job_id")
            new_status = data.get("status")

            logger.debug(f"Received job_id: {job_id}, new_status: {new_status}")  # Log received data

            if not job_id or not new_status:
                logger.error("Missing job_id or status")  # Log error if job_id or status is missing
                return JsonResponse({"success": False, "error": "Missing job ID or status"}, status=400)

            try:
                job = Job.objects.get(id=job_id)
                logger.debug(f"Found job: {job.title} with current status: {job.status}")  # Log job details
            except Job.DoesNotExist:
                logger.error(f"Job with id {job_id} does not exist.")
                return JsonResponse({"success": False, "error": "Job not found"}, status=404)

            job.status = new_status
            job.save()
            logger.debug(f"Job status updated to: {job.status}")  # Log successful status update

            # If the job is approved, send a notification
            if new_status.lower() == "approved" and job.employer:
                EmployerNotification.objects.create(
                    employer=job.employer,
                    title="Job Approved",
                    message=f"🎉 Your job listing '{job.title}' has been approved!",
                    is_read=False
                )

            return JsonResponse({"success": True})

        except Exception as e:
            logger.error(f"Unexpected error occurred: {str(e)}")  # Log any unexpected errors
            return JsonResponse({"success": False, "error": f"An unexpected error occurred: {str(e)}"}, status=500)

    logger.error("Invalid request method")  # Log if request method is not POST
    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)



@csrf_exempt
@user_passes_test(is_admin)
def resolve_feedback(request, feedback_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST method is allowed'}, status=405)
    
    try:
        notification = Notification.objects.get(id=feedback_id, notification_type='feedback')
        
        # Mark notification as read and change priority
        notification.is_read = True
        notification.priority = 'low'  # Lower priority
        notification.save()
        
        return JsonResponse({'status': 'success'})
    except Notification.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Feedback not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)