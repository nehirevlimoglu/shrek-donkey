from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from tutorials.models.admin_models import Admin
from tutorials.models.admin_models import Notification
from django.http import JsonResponse, HttpResponse
from tutorials.models.user_model import User
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
import json
from tutorials.models.employer_models import Job, Candidate, Employer
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import json
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404  # Added get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages  # Added messages import
from tutorials.models.admin_models import Admin, Notification
from tutorials.models.employer_models import EmployerNotification 
from tutorials.models.employer_models import Job



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


def review_job(request, job_id, decision):
    """Admin action to approve or reject job listings."""
    job = get_object_or_404(Job, id=job_id)

    if decision == 'approve':
        job.status = 'approved'
        job.save(update_fields=['status'])  # ✅ Ensure only status updates
        messages.success(request, f"✅ {job.title} has been approved!")

    elif decision == 'reject':
        job.status = 'rejected'
        job.save(update_fields=['status'])
        messages.error(request, f"❌ {job.title} has been rejected!")

    print(f"🔄 Job '{job.title}' updated to status: {job.status}")  # Debugging log

    return redirect('admin_job_listings')  # Redirect to admin job listings

def admin_settings(request):
    if not request.user.is_authenticated:
        return redirect('log-in')
    
    if request.user.role != 'Admin':
        return HttpResponse("Access Denied: You are not authorized to access this page.", status=403)
    
    try:
        # Try to get the Admin object
        admin = Admin.objects.get(id=request.user.id)
    except Admin.DoesNotExist:
        # If Admin object doesn't exist, create it based on the existing User
        try:
            admin = Admin(
                id=request.user.id,
                username=request.user.username,
                email=request.user.email,
                first_name=request.user.first_name,
                last_name=request.user.last_name,
                password=request.user.password,
                role='Admin'
            )
            admin.save()
        except Exception as e:
            # Log the error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create Admin object: {str(e)}")
            # Return a more user-friendly error message
            return render(request, 'admin_settings.html', {
                'admin': request.user,
                'error': 'We encountered a problem with your admin profile. Some features may be limited.',
                'tab': request.GET.get('tab', 'profile')
            })
    
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            admin.username = request.POST.get('username')
            admin.email = request.POST.get('email')
            admin.first_name = request.POST.get('first_name')
            admin.last_name = request.POST.get('last_name')
            admin.phone_number = request.POST.get('phone_number', '')
            admin.save()
            
            # Update the User object as well
            user = request.user
            user.username = admin.username
            user.email = admin.email
            user.first_name = admin.first_name
            user.last_name = admin.last_name
            user.save()
            
            # Create success notification
            Notification.objects.create(
                recipient=request.user,
                title="Profile Updated",
                message="Your admin profile has been successfully updated.",
                notification_type='system',
                priority='low',
                is_read=False
            )
            
            return redirect('admin_settings')
        
        elif 'change_password' in request.POST:
            # Get password data
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            # Verify current password
            if not request.user.check_password(current_password):
                return render(request, 'admin_settings.html', {
                    'admin': admin,
                    'error': 'Current password is incorrect.',
                    'tab': 'password'
                })
            
            # Check if new passwords match
            if new_password != confirm_password:
                return render(request, 'admin_settings.html', {
                    'admin': admin,
                    'error': 'New passwords do not match.',
                    'tab': 'password'
                })
            
            # Update password for both Admin and User
            admin.set_password(new_password)
            admin.save()
            
            request.user.set_password(new_password)
            request.user.save()
            
            # Create success notification
            Notification.objects.create(
                recipient=request.user,
                title="Password Changed",
                message="Your password has been successfully changed.",
                notification_type='system',
                priority='medium',
                is_read=False
            )
            
            # Re-authenticate user with new password
            user = authenticate(username=admin.username, password=new_password)
            if user:
                login(request, user)
            
            return redirect('admin_settings')
            
        elif 'update_notification_prefs' in request.POST:
            # Get checkbox values
            job_notifications = request.POST.get('job_notifications') == 'on'
            application_notifications = request.POST.get('application_notifications') == 'on'
            user_notifications = request.POST.get('user_notifications') == 'on'
            system_notifications = request.POST.get('system_notifications') == 'on'
            
            email_delivery = request.POST.get('email_delivery') == 'on'
            dashboard_delivery = request.POST.get('dashboard_delivery') == 'on'
            
            # Create notification types and delivery methods lists
            notification_types = []
            if job_notifications:
                notification_types.append("job listings")
            if application_notifications:
                notification_types.append("applications")
            if user_notifications:
                notification_types.append("user accounts")
            if system_notifications:
                notification_types.append("system updates")
                
            delivery_methods = []
            if email_delivery:
                delivery_methods.append("email")
            if dashboard_delivery:
                delivery_methods.append("dashboard")
                
            # Create notification message
            notification_message = f"You will receive notifications for: {', '.join(notification_types)}. "
            notification_message += f"Delivery methods: {', '.join(delivery_methods)}."
            
            Notification.objects.create(
                recipient=request.user,
                title="Notification Preferences Updated",
                message=notification_message,
                notification_type='system',
                priority='low',
                is_read=False
            )
            
            return redirect('admin_settings?tab=notifications')
    
    # For GET requests or after processing POST
    return render(request, 'admin_settings.html', {
        'admin': admin,
        'tab': request.GET.get('tab', 'profile')
    })


@user_passes_test(is_admin)
def admin_notifications(request):
    # Get filter parameters
    notification_type = request.GET.get('type', 'all')
    priority = request.GET.get('priority', 'all')
    is_read = request.GET.get('is_read', 'all')
    search_query = request.GET.get('search', '')
    
    # Base query - exclude soft-deleted notifications
    notifications_query = Notification.objects.filter(
        recipient=request.user,
        is_deleted=False
    )
    
    # Apply type filter
    if notification_type != 'all':
        notifications_query = notifications_query.filter(notification_type=notification_type)
    
    # Apply priority filter
    if priority != 'all':
        notifications_query = notifications_query.filter(priority=priority)
    
    # Apply read status filter
    if is_read == 'read':
        notifications_query = notifications_query.filter(is_read=True)
    elif is_read == 'unread':
        notifications_query = notifications_query.filter(is_read=False)
    
    # Apply search filter
    if search_query:
        notifications_query = notifications_query.filter(
            Q(title__icontains=search_query) | 
            Q(message__icontains=search_query)
        )
    
    # Get notification statistics
    total_count = Notification.objects.filter(recipient=request.user, is_deleted=False).count()
    unread_count = Notification.objects.filter(recipient=request.user, is_read=False, is_deleted=False).count()
    
    # Get notification type counts for filtering UI
    type_counts = {
        'job': Notification.objects.filter(recipient=request.user, notification_type='job', is_deleted=False).count(),
        'application': Notification.objects.filter(recipient=request.user, notification_type='application', is_deleted=False).count(),
        'user': Notification.objects.filter(recipient=request.user, notification_type='user', is_deleted=False).count(),
        'system': Notification.objects.filter(recipient=request.user, notification_type='system', is_deleted=False).count(),
        'general': Notification.objects.filter(recipient=request.user, notification_type='general', is_deleted=False).count(),
    }
    
    # Get priority counts
    priority_counts = {
        'high': Notification.objects.filter(recipient=request.user, priority='high', is_deleted=False).count(),
        'medium': Notification.objects.filter(recipient=request.user, priority='medium', is_deleted=False).count(),
        'low': Notification.objects.filter(recipient=request.user, priority='low', is_deleted=False).count(),
    }
    
    # Order by creation date (newest first)
    notifications_query = notifications_query.order_by('-created_at')
    
    # Enhanced pagination with items per page option
    items_per_page = request.GET.get('items_per_page', 10)
    try:
        items_per_page = int(items_per_page)
        if items_per_page not in [5, 10, 25, 50]:
            items_per_page = 10  # Default if invalid value
    except ValueError:
        items_per_page = 10  # Default if not a number
    
    page = request.GET.get('page', 1)
    paginator = Paginator(notifications_query, items_per_page)
    
    try:
        notifications_page = paginator.page(page)
    except PageNotAnInteger:
        notifications_page = paginator.page(1)
    except EmptyPage:
        notifications_page = paginator.page(paginator.num_pages)
    
    # Calculate page ranges for pagination UI
    # Show first page, last page, and 2 pages before and after current page
    page_range = []
    current_page = notifications_page.number
    total_pages = paginator.num_pages
    
    # Always include first and last page
    if total_pages > 1:
        page_range.append(1)
        
        # Add pages around current page
        for i in range(max(2, current_page - 2), min(current_page + 3, total_pages + 1)):
            if i - 1 not in page_range:
                if i - 1 > 1:
                    page_range.append('...')
            page_range.append(i)
            
        # Add last page if not already included
        if total_pages > 1 and total_pages not in page_range:
            if total_pages - 1 not in page_range:
                page_range.append('...')
            page_range.append(total_pages)
    
    return render(request, 'admin_notifications.html', {
        'notifications': notifications_page,
        'total_count': total_count,
        'unread_count': unread_count,
        'type_counts': type_counts,
        'priority_counts': priority_counts,
        'notification_type': notification_type,
        'priority': priority,
        'is_read': is_read,
        'search_query': search_query,
        'items_per_page': items_per_page,
        'page_range': page_range,
        'paginator': paginator,  # 添加paginator到上下文中
    })

@user_passes_test(is_admin)
def admin_notifications_count(request):
    """Return the count of unread notifications for the admin user"""
    unread_count = Notification.objects.filter(recipient=request.user, is_read=False, is_deleted=False).count()
    return JsonResponse({'count': unread_count})

@user_passes_test(is_admin)
@require_POST
def mark_notification_as_read(request, notification_id):
    """Mark a single notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'success'})

@user_passes_test(is_admin)
@require_POST
def mark_all_notifications_as_read(request):
    """Mark all notifications as read for the current user"""
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'success'})

@user_passes_test(is_admin)
@require_POST
def delete_notification(request, notification_id):
    """Soft delete a notification (mark as deleted)"""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_deleted = True
    notification.save()
    return JsonResponse({'status': 'success'})

@user_passes_test(is_admin)
@require_POST
def delete_all_notifications(request):
    """Soft delete all notifications for the current user"""
    Notification.objects.filter(recipient=request.user).update(is_deleted=True)
    return JsonResponse({'status': 'success'})

@user_passes_test(is_admin)
def generate_admin_notification(request):
    """Generate a test notification for the admin user"""
    Notification.objects.create(
        recipient=request.user,
        title="Test Notification",
        message="This is a test notification for admin users.",
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
            
            # Problem: The currently logged-in user might not be counted
            # Solution: 1. Use the date part of last_login instead of the exact timestamp
            #           2. Ensure that users logged in today are included
            if i == 0:  # Today
                # Special handling for today's data to include the current user
                # Count all users who logged in today
                users_today = User.objects.filter(
                    last_login__date=today
                ).count()
                
                # If the current user is logged in but not yet recorded in the database, add 1
                if request.user.is_authenticated and request.user.last_login and request.user.last_login.date() < today:
                    users_today += 1
                
                count = users_today
            else:
                # Data for past days
                count = User.objects.filter(
                    last_login__date=day
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
            
            # Improved counting method using date queries
            if i == 0:  # Current week
                # Get the number of users logged in this week
                query = Q(last_login__date__gte=week_start, last_login__date__lt=week_end)
                users_this_week = User.objects.filter(query).count()
                
                # If the current user is logged in but last_login is not within this week, add 1
                if request.user.is_authenticated and request.user.last_login:
                    user_last_login_date = request.user.last_login.date()
                    if user_last_login_date < week_start:
                        users_this_week += 1
                
                count = users_this_week
            else:
                # Data for past weeks
                count = User.objects.filter(
                    last_login__date__gte=week_start,
                    last_login__date__lt=week_end
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
            
            # Similarly improve monthly counting
            if i == 0:  # Current month
                # Get the number of users logged in this month
                users_this_month = User.objects.filter(
                    last_login__date__gte=month_date,
                    last_login__date__lt=next_month
                ).count()
                
                # If the current user is logged in but last_login is not within this month, add 1
                if request.user.is_authenticated and request.user.last_login:
                    user_last_login_date = request.user.last_login.date()
                    if user_last_login_date < month_date:
                        users_this_month += 1
                
                count = users_this_month
            else:
                # Data for past months
                count = User.objects.filter(
                    last_login__date__gte=month_date,
                    last_login__date__lt=next_month
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
    
    # Enhanced pagination with items per page option
    items_per_page = request.GET.get('items_per_page', 10)
    try:
        items_per_page = int(items_per_page)
        if items_per_page not in [5, 10, 25, 50]:
            items_per_page = 10  # Default if invalid value
    except ValueError:
        items_per_page = 10  # Default if not a number
    
    page = request.GET.get('page', 1)
    paginator = Paginator(applications_query, items_per_page)
    
    try:
        applications_page = paginator.page(page)
    except PageNotAnInteger:
        applications_page = paginator.page(1)
    except EmptyPage:
        applications_page = paginator.page(paginator.num_pages)
    
    # Calculate page ranges for pagination UI
    # Show first page, last page, and 2 pages before and after current page
    page_range = []
    current_page = applications_page.number
    total_pages = paginator.num_pages
    
    # Always include first and last page
    if total_pages > 1:
        page_range.append(1)
        
        # Add pages around current page
        for i in range(max(2, current_page - 2), min(current_page + 3, total_pages + 1)):
            if i - 1 not in page_range:
                if i - 1 > 1:
                    page_range.append('...')
            page_range.append(i)
            
        # Add last page if not already included
        if total_pages > 1 and total_pages not in page_range:
            if total_pages - 1 not in page_range:
                page_range.append('...')
            page_range.append(total_pages)
    
    return render(request, 'admin_applications_view.html', {
        'applications': applications_page,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'interview_applications': interview_applications,
        'hired_applications': hired_applications,
        'rejected_applications': rejected_applications,
        'items_per_page': items_per_page,
        'page_range': page_range,
    })


@csrf_exempt 
def update_job_status(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            job_id = data.get("job_id")
            new_status = data.get("status")

            job = Job.objects.get(id=job_id)
            job.status = new_status
            job.save()

            # ✅ Create a notification in EmployerNotification model
            if new_status.lower() == "approved":
                if job.employer:  # Ensure job has an employer
                    EmployerNotification.objects.create(
                        employer=job.employer,  # ✅ Uses the new employer-specific notification model
                        title="Job Approved",
                        message=f"🎉 Your job listing '{job.title}' has been approved!",
                        is_read=False
                    )
                else:
                    return JsonResponse({"success": False, "error": "Job has no employer"})

            return JsonResponse({"success": True})
        except Job.DoesNotExist:
            return JsonResponse({"success": False, "error": "Job not found"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)
