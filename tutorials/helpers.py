from django.conf import settings
from django.shortcuts import redirect
from django.contrib import messages

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

# Function to clear feedback-related messages
def clear_feedback_messages(request):
    """
    Clear any feedback-related messages from the messages framework.
    This is useful to prevent feedback messages from appearing in login pages.
    """
    storage = messages.get_messages(request)
    to_keep = []
    
    # Iterate through messages
    for message in storage:
        # If message contains feedback, don't add it to keep list
        if "feedback" not in str(message).lower():
            to_keep.append(message)
    
    # Reset storage and add back non-feedback messages
    storage.used = True  # Mark all current messages as used to clear them
    
    # Add back messages we want to keep
    for message in to_keep:
        if message.level == messages.DEBUG:
            messages.debug(request, message.message)
        elif message.level == messages.INFO:
            messages.info(request, message.message)
        elif message.level == messages.SUCCESS:
            messages.success(request, message.message)
        elif message.level == messages.WARNING:
            messages.warning(request, message.message)
        elif message.level == messages.ERROR:
            messages.error(request, message.message)
