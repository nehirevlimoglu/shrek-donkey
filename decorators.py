from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse
from functools import wraps
from django.http import Http404

def admin_only(view_func):
    """Admin only access """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # If not an admin user, raise 404 (unchanged)
        if not request.user.role == "Admin":
            raise Http404("You are not authorized to view this page.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def employer_only(view_func):
    """Employer only access """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # If not an employer user, raise 404 (unchanged)
        if not request.user.role == "Employer":
            raise Http404("You are not authorized to view this page.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def applicant_only(view_func):
    """Applicant and Job Seeker Only Access"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # 1) If user not logged in => redirect to login page
        if not request.user.is_authenticated:
            return redirect(f"{reverse('log-in')}?next={request.path}")

        # 2) If logged in but not applicant/job_seeker => raise 403
        if getattr(request.user, 'role', None) not in ["Applicant", "job_seeker"]:
            raise PermissionDenied("You are not authorized to view this page.")

        # Otherwise, user can access the view
        return view_func(request, *args, **kwargs)
    return _wrapped_view
