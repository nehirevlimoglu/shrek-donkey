from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from tutorials.models.admin_models import Admin, Notification
from tutorials.models.employer_models import Job


def is_admin(user):
    return user.role == 'Admin'

@user_passes_test(is_admin)
def admin_home_page(request):
    admins = Admin.objects.all()  # Your existing data
    return render(request, 'admin_home_page.html', {
        'admins': admins,
    })

def admin_job_listings(request):
    """Admin page to review only pending job listings."""
    pending_jobs = Job.objects.filter(status='pending')  # Only fetch jobs that are pending
    return render(request, 'admin_job_listings.html', {'pending_jobs': pending_jobs})

def review_job(request, job_id, decision):
    """Admin action to approve or reject job listings."""
    job = get_object_or_404(Job, id=job_id)

    if decision == 'approve':
        job.status = 'approved'
        job.save(update_fields=['status'])  # ✅ Force Django to save only the status field
        messages.success(request, f"✅ {job.title} has been approved!")
    elif decision == 'reject':
        job.status = 'rejected'
        job.save(update_fields=['status'])  # ✅ Force saving rejection
        messages.error(request, f"❌ {job.title} has been rejected!")

    print(f"🔄 Job '{job.title}' updated to status: {job.status}")  # Debugging log

    return redirect('admin_job_listings')  # Redirect to admin job listings

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

