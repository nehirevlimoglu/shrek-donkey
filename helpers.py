from django.conf import settings
from django.shortcuts import redirect

def login_prohibited(view_function):
    """Decorator for view functions that redirect users based on their role if they are logged in."""

    def modified_view_function(request):
        if request.user.is_authenticated:
            if request.user.role == 'Admin':
                return redirect(settings.REDIRECT_URL_WHEN_LOGGED_IN_ADMIN)
            elif request.user.role == 'Applicant':
                return redirect(REDIRECT_URL_WHEN_LOGGED_IN_APPLICANTS)
            elif:
                return redirect(settings.REDIRECT_URL_WHEN_LOGGED_IN_EMPLOYER)
            else:
                return redirect(settings.REDIRECT_URL_WHEN_LOGGED_IN)

    return modified_view_function

