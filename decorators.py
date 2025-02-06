from django.http import Http404
from functools import wraps

def admin_only(view_func):
    """Admin only access """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.role == "Admin":
            raise Http404("You are not authroized to view this page.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def employer_only(view_func):
    """Employer only access """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.role == "Employer":
            raise Http404("You are not authroized to view this page.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

    
def applicant_only(view_func):
    """Applicant only access """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.role == "Applicant":
            raise Http404("You are not authroized to view this page.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

    
    
