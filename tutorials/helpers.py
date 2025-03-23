from django.conf import settings
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.messages import get_messages

def login_prohibited(view_function):
    """Decorator for view functions that redirect users based on their role if they are logged in."""

    def modified_view_function(request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.role == 'Admin':
                return redirect(settings.REDIRECT_URL_WHEN_LOGGED_IN_ADMIN)
            elif request.user.role == 'Applicant':
                return redirect(settings.REDIRECT_URL_WHEN_LOGGED_IN_APPLICANT)  # Fixed reference
            elif request.user.role == 'Employer':
                return redirect(settings.REDIRECT_URL_WHEN_LOGGED_IN_EMPLOYER)
            else:
                return redirect(settings.REDIRECT_URL_WHEN_LOGGED_IN)

        return view_function(request, *args, **kwargs)

    return modified_view_function

from django.contrib.messages import get_messages

def clear_feedback_messages(request):
    """
    Removes all messages except ones tagged 'login' — does NOT re-add anything.
    """
    storage = get_messages(request)
    # Mark only non-login ones as used
    storage._queued_messages = [m for m in storage if 'login' in m.tags]



def create_admin_notification(
    user,
    title,
    message,
    notification_type='general',
    priority='medium',
    related_object_id=None,
    related_object_type=None,
    action_url=None
):
    """
    Enhanced utility function to create notifications for admin users
    but prevents creating duplicates with the same fields.
    """
    if user.role == 'Admin':
        # Check if an identical (non-deleted) notification already exists
        existing = Notification.objects.filter(
            recipient=user,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            related_object_id=related_object_id,
            related_object_type=related_object_type,
            action_url=action_url,
            is_deleted=False
        )
        if not existing.exists():
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