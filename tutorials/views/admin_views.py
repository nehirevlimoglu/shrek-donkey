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
from django.core.cache import cache
from django.contrib.auth.decorators import login_required
from tutorials.forms.forms import CustomPasswordChangeForm
from tutorials.forms.admin_forms import AdminProfileForm
from django.urls import reverse

def is_admin(user):
    return bool(user) and getattr(user, 'role', None) == 'Admin'


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
def admin_notifications(request):
    # Get query parameters
    notification_type = request.GET.get('type', 'all')
    priority = request.GET.get('priority', 'all')
    is_read = request.GET.get('is_read', 'all')
    search_query = request.GET.get('search', '')
    page = request.GET.get('page', 1)
    
    # Base queryset: filter by recipient = current admin user
    notifications = Notification.objects.filter(
        recipient=request.user,      # <--- filter by the logged-in admin
        is_deleted=False
    )
    
    # Apply filters as before
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
    
    # Count totals for statistics (only among this admin’s notifications)
    total_count = notifications.count()
    unread_count = notifications.filter(is_read=False).count()
    
    # Count by type and priority
    type_counts = {
        'general': notifications.filter(notification_type='general').count(),
        'job': notifications.filter(notification_type='job').count(),
        'application': notifications.filter(notification_type='application').count(),
        'user': notifications.filter(notification_type='user').count(),
        'system': notifications.filter(notification_type='system').count(),
    }
    
    priority_counts = {
        'high': notifications.filter(priority='high').count(),
        'medium': notifications.filter(priority='medium').count(),
        'low': notifications.filter(priority='low').count(),
    }
    
    # Paginate
    paginator = Paginator(notifications, 10)
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
        'type_counts': type_counts,
        'priority_counts': priority_counts,
    }
    
    return render(request, 'admin_notifications.html', context)

@user_passes_test(is_admin)
def admin_notifications_count(request):
    # Count only unread notifications for this specific Admin
    unread_count = Notification.objects.filter(
        recipient=request.user,
        is_read=False,
        is_deleted=False
    ).count()
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
    notification_types = ['general', 'job', 'application', 'user', 'system']
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

    job.refresh_from_db()

    logger.debug(f"[admin_job_detail] Job ID: {job.id}, Title: {job.title}")
    logger.debug(f"[admin_job_detail] Application deadline: {job.application_deadline}")
    logger.debug(f"[admin_job_detail] Current date: {timezone.now().date()}")
    logger.debug(f"[admin_job_detail] Job status from DB: {job.status}")

    today = timezone.now().date()
    if job.application_deadline:
        if job.application_deadline <= today:
            job.is_open = False
            logger.debug("[admin_job_detail] Job marked as closed because deadline has passed or is today")
        else:
            job.is_open = True
            logger.debug("[admin_job_detail] Job marked as open because deadline is in the future")
    else:
        if job.status == 'rejected':
            job.is_open = False
            logger.debug("[admin_job_detail] Job marked as closed because status is rejected")
        else:
            job.is_open = True
            logger.debug("[admin_job_detail] Job marked as open because no deadline and not rejected")

    job.display_status = "Open" if job.is_open else "Closed"
    logger.debug(f"[admin_job_detail] Final display status: {job.display_status}")

    # ✅ Create a notification if job is approved or rejected and no notification has been sent ye

    if job.status in ['approved', 'rejected'] and employer:
        title = "Job Listing Approved " if job.status == 'approved' else "Job Listing Rejected "
        message = f"Your job listing '{job.title}' has been {job.status}."

        already_exists = EmployerNotification.objects.filter(
            employer=employer,
            title=title,
        ).exists()

        if not already_exists:
            EmployerNotification.objects.create(
                employer=employer,
                title=title,
                message=message,
                is_read=False
            )
            logger.debug(f"[admin_job_detail] EmployerNotification created for job '{job.title}' to employer '{employer.user.username}'")

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
    
    logger.debug(f"Toggle job status: job_id={job_id}, status={status}")
    
    if status == 'Closed':
        # Set deadline to yesterday to ensure it's definitely closed
        job.application_deadline = timezone.now().date() - timedelta(days=1)
        logger.debug(f"Closing job: setting deadline to {job.application_deadline}")
    elif status == 'Open':
        # Set deadline to a future date to indicate job is open
        job.application_deadline = timezone.now().date() + timedelta(days=30)
        logger.debug(f"Opening job: setting deadline to {job.application_deadline}")
    elif status == 'Approved':
        # Update the job status to approved
        job.status = 'approved'
        logger.debug(f"Approving job: setting status to approved")
        # Ensure the deadline is in the future for approved jobs
        if not job.application_deadline or job.application_deadline < timezone.now().date():
            job.application_deadline = timezone.now().date() + timedelta(days=30)
            logger.debug(f"Approved job: setting deadline to {job.application_deadline}")
    
    job.save()
    
    return JsonResponse({'success': True})

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

@user_passes_test(is_admin)
def get_candidate_info(request, candidate_id):
    """
    Get detailed information about a candidate for the modal view.
    This endpoint is called by the view-candidate-btn in admin_job_detail.html.
    """
    logger.debug(f"[get_candidate_info] Request method: {request.method}, Candidate ID: {candidate_id}")
    logger.debug(f"[get_candidate_info] Path: {request.path}, User: {request.user}")
    
    try:
        logger.debug(f"[get_candidate_info] Fetching info for candidate ID: {candidate_id}")
        candidate = Candidate.objects.get(id=candidate_id)
        logger.debug(f"[get_candidate_info] Found candidate: {candidate}")
        
        # Get candidate data to return as JSON
        candidate_data = {
            'id': candidate.id,
            'name': f"{candidate.user.first_name} {candidate.user.last_name}" if candidate.user.first_name else candidate.user.username,
            'email': candidate.user.email,
            'application_date': candidate.application_date.strftime('%Y-%m-%d') if candidate.application_date else '',
            'status': candidate.application_status,
            # Add more fields as needed
            'phone': candidate.phone or 'Not provided',
            'degree': candidate.degree or 'Not provided',
            'school': candidate.school or 'Not provided',
            'skills': candidate.skills or '[]'
        }
        
        logger.debug(f"[get_candidate_info] Returning data: {candidate_data}")
        response = JsonResponse(candidate_data)
        
        # Add CORS headers for development
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Allow-Headers"] = "X-Requested-With, Content-Type"
        
        return response
    except Candidate.DoesNotExist:
        logger.error(f"[get_candidate_info] Candidate with ID {candidate_id} not found")
        return JsonResponse({'error': 'Candidate not found'}, status=404)
    except Exception as e:
        logger.error(f"[get_candidate_info] Error: {str(e)}")
        import traceback
        logger.error(f"[get_candidate_info] Traceback: {traceback.format_exc()}")
        return JsonResponse({'error': str(e)}, status=500)


@user_passes_test(is_admin)
@require_POST
def update_candidate_status(request, candidate_id):
    """
    Update a candidate's application status.
    This endpoint is called by the Update Status button in the candidate modal.
    """
    try:
        logger.debug(f"[update_candidate_status] Updating status for candidate ID: {candidate_id}")
        data = json.loads(request.body)
        new_status = data.get('status')
        logger.debug(f"[update_candidate_status] New status: {new_status}")
        
        if not new_status:
            logger.error("[update_candidate_status] Missing status in request")
            return JsonResponse({'error': 'Status is required'}, status=400)
        
        # Get the valid status choices
        valid_statuses = [status[0] for status in Candidate.STATUS_CHOICES]
        logger.debug(f"[update_candidate_status] Valid statuses: {valid_statuses}")
        
        if new_status not in valid_statuses:
            logger.error(f"[update_candidate_status] Invalid status: {new_status}")
            return JsonResponse({'error': f'Invalid status. Valid options are: {", ".join(valid_statuses)}'}, status=400)
        
        candidate = Candidate.objects.get(id=candidate_id)
        logger.debug(f"[update_candidate_status] Found candidate: {candidate}")
        
        # Update the status
        candidate.application_status = new_status
        candidate.save()
        logger.debug(f"[update_candidate_status] Status updated successfully to: {new_status}")
        
        return JsonResponse({'success': True})
    except Candidate.DoesNotExist:
        logger.error(f"[update_candidate_status] Candidate with ID {candidate_id} not found")
        return JsonResponse({'error': 'Candidate not found'}, status=404)
    except json.JSONDecodeError:
        logger.error("[update_candidate_status] Invalid JSON in request body")
        return JsonResponse({'error': 'Invalid JSON in request body'}, status=400)
    except Exception as e:
        logger.error(f"[update_candidate_status] Error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

import logging
logger = logging.getLogger(__name__)


@csrf_exempt
def update_job_status(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            job_id = data.get("job_id")
            new_status = data.get("status")

            logger.debug(f"[update_job_status] Received job_id: {job_id}, new_status: {new_status}")  # Log received data

            if not job_id or not new_status:
                logger.error("[update_job_status] Missing job_id or status")  # Log error if job_id or status is missing
                return JsonResponse({"success": False, "error": "Missing job ID or status"}, status=400)

            try:
                job = Job.objects.get(id=job_id)
                logger.debug(f"[update_job_status] Found job: {job.title} with current status: {job.status}")  # Log job details
                logger.debug(f"[update_job_status] Current application deadline: {job.application_deadline}")
            except Job.DoesNotExist:
                logger.error(f"[update_job_status] Job with id {job_id} does not exist.")
                return JsonResponse({"success": False, "error": "Job not found"}, status=404)

            original_status = job.status
            original_deadline = job.application_deadline
            
            # Handle special cases for Open/Closed (which affect the deadline)
            if new_status == 'Open':
                # Set deadline to a future date to indicate job is open
                job.application_deadline = timezone.now().date() + timedelta(days=30)
                logger.debug(f"[update_job_status] Setting deadline to future: {job.application_deadline}")
                
                if job.status == 'pending':
                    # Keep the pending status if it was pending
                    pass
                elif job.status == 'rejected':
                    # If rejected, move back to pending
                    job.status = 'pending'
                # The 'approved' status should be preserved if it was already approved
            elif new_status == 'Closed':
                # Set deadline to TWO DAYS AGO to ensure it's definitely closed
                # This fixes the issue where today's date might be interpreted as still open
                job.application_deadline = timezone.now().date() - timedelta(days=2)
                logger.debug(f"[update_job_status] Setting deadline to 2 days ago: {job.application_deadline} to ensure closure")
                # Don't change the actual status field
            elif new_status.lower() == 'approved':
                # Change the job's status to approved
                job.status = 'approved'
                # Ensure the deadline is in the future
                if not job.application_deadline or job.application_deadline < timezone.now().date():
                    job.application_deadline = timezone.now().date() + timedelta(days=30)
                    logger.debug(f"[update_job_status] Approved job: setting deadline to {job.application_deadline}")
            elif new_status.lower() == 'rejected':
                job.status = 'rejected'
                # Set the deadline to yesterday to close the job
                job.application_deadline = timezone.now().date() - timedelta(days=2)
                logger.debug(f"[update_job_status] Rejected job: setting deadline to {job.application_deadline}")
            else:
                # For any other status we don't recognize, just keep the changes minimal
                logger.warning(f"[update_job_status] Unrecognized status: {new_status}")

            job.save()
            logger.debug(f"[update_job_status] Job updated: status changed from {original_status} to {job.status}")
            logger.debug(f"[update_job_status] Deadline changed from {original_deadline} to {job.application_deadline}")

            # If the job is approved, send a notification
            if new_status.lower() in ["approved", "rejected"] and job.employer:
                print("[DEBUG] Hitting approved block in update_job_status")

                Notification.objects.create(
                    recipient=job.employer.user,
                    sender=request.user,  # the admin performing the action
                    title=f"Job Listing {new_status.capitalize()}",
                    message=(
                        f"Your job listing '{job.title}' has been {new_status.lower()} by the admin team."
                        if new_status.lower() == "approved"
                        else f"Unfortunately, your job listing '{job.title}' was rejected."
                    ),
                    notification_type=Notification.TYPE_JOB,
                    priority=Notification.PRIORITY_HIGH if new_status.lower() == "rejected" else Notification.PRIORITY_MEDIUM,
                    related_object_id=job.id,
                    related_object_type='Job',
                    action_url=f"/job_detail/{job.id}/"  # adjust to your actual job detail route
                )
                logger.debug(f"[update_job_status] Sent '{new_status}' notification to employer {job.employer.user.username}")


            try:
                cache.delete(f'job_{job_id}_status')
                logger.debug(f"[update_job_status] Cleared cache for job_{job_id}_status")
            except Exception as e:
                logger.error(f"[update_job_status] Error clearing cache: {str(e)}")

            return JsonResponse({"success": True})
        except Exception as e:
            logger.error(f"[update_job_status] Unexpected error: {str(e)}")
            return JsonResponse({"success": False, "error": str(e)}, status=500)
    
    return JsonResponse({"success": False, "error": "Method not allowed"}, status=405)


@login_required
def admin_settings(request):
    tab = request.GET.get('tab', 'profile')
    admin_user = get_object_or_404(Admin, user=request.user)

    form = None
    password_form = None

    # Profile editing
    if tab == 'change-profile':
        if request.method == 'POST':
            form = AdminProfileForm(request.POST, instance=admin_user, user=request.user)
            if form.is_valid():
                form.save()
                request.user.refresh_from_db()
                messages.success(request, "Admin profile updated successfully.")
                return redirect('admin_settings')
        else:
            form = AdminProfileForm(instance=admin_user, user=request.user)

    # Password changing
    elif tab == 'password':
        form = CustomPasswordChangeForm(user=request.user)
        if request.method == 'POST':
            form = CustomPasswordChangeForm(user=request.user, data=request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Password changed successfully.")
                return redirect('admin_settings')

    context = {
        'tab': tab,
        'admin_user': admin_user,
        'form': form,
        'password_form': password_form,
        'user': request.user,
    }
    return render(request, 'admin_settings.html', context)
