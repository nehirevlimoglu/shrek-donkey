from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse  # Used for redirection
from django.contrib.auth.decorators import login_required
from tutorials.helpers import login_prohibited, clear_feedback_messages  # If used elsewhere
from tutorials.forms.forms import SignUpForm  # Form for signing up
from tutorials.forms.applicants_forms import ApplicantForm  # Applicant profile completion form
from tutorials.forms.employer_forms import EmployerProfileForm  # Employer profile completion form
from tutorials.models.applicants_models import Applicant  # Applicant model
from tutorials.models.employer_models import Employer  # Employer model
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.middleware.csrf import get_token
from tutorials.models.employer_models import Job
from tutorials.utils import match_candidates_to_job

# Custom CSRF failure view
def csrf_failure(request, reason=""):
    """
    Custom CSRF validation failure view
    """
    print(f"CSRF validation failed, reason: {reason}")
    
    # Force generate a new CSRF token
    get_token(request)
    
    # Add error message
    messages.error(request, f"Form submission failed (CSRF validation error): {reason}")
    
    # Clear any feedback messages
    clear_feedback_messages(request)
    
    # Render login page and force set new CSRF cookie
    response = render(request, 'log_in.html')
    response.set_cookie('csrftoken', request.META.get('CSRF_COOKIE', ''), samesite=None)
    return response


@csrf_exempt  # Temporarily disable CSRF protection, only for testing purposes
@ensure_csrf_cookie
def log_in(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        print(f"Attempting login: {username} | {password}")  # ✅ Debugging step
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            print(f"User authenticated: {user.username} | Role: {user.role}")  # ✅ Debugging step
            login(request, user)

            # ✅ Redirect based on role
            if request.user.role == 'Admin':
                return redirect('admin_home_page')  
            elif request.user.role == 'Employer':
                return redirect('employer_home_page')  
            elif request.user.role == 'Applicant' or request.user.role == 'job_seeker':               
                return redirect('applicants-home-page')  
            
            raise Http404("Page not found")
        else:
            print("Authentication failed")  # ❌ This means the username/password is incorrect.
            # Add error message
            messages.error(request, "Incorrect username or password")
    
    # Clear any feedback messages before rendering login page
    clear_feedback_messages(request)
    
    # Force set CSRF Cookie
    response = render(request, 'log_in.html')
    response.set_cookie('csrftoken', request.META.get('CSRF_COOKIE', ''), samesite='Lax')
    return response


def sign_up(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            # ✅ Ensure employer or applicant profile is created immediately
            if user.role == 'Employer':
                Employer.objects.create(user=user, username=user.username, email=user.email)  # ✅ Auto-create profile
                return redirect('employer_profile_setup')

            elif user.role == 'Applicant':
                Applicant.objects.create(user=user)  # ✅ Auto-create profile
                return redirect('applicant_profile_setup')

            return redirect('home')

    else:
        form = SignUpForm()

    return render(request, 'sign_up.html', {'form': form})


@login_required
def applicant_profile_setup(request):
    try:
        applicant = request.user.applicant
    except Applicant.DoesNotExist:
        applicant = None

    if request.method == 'POST':
        form = ApplicantForm(request.POST, request.FILES, user=request.user, instance=applicant)
        if form.is_valid():
            applicant = form.save(commit=False)
            applicant.user = request.user
            applicant.save()
            return redirect('applicants-home-page')  # ✅ Redirect AFTER profile completion

    else:
        form = ApplicantForm(user=request.user, instance=applicant)

    return render(request, 'applicant_profile_setup.html', {'form': form})

@login_required
def employer_profile_setup(request):
    try:
        employer = request.user.employer
    except Employer.DoesNotExist:
        employer = None

    if request.method == 'POST':
        form = EmployerProfileForm(request.POST, request.FILES, instance=employer)
        if form.is_valid():
            employer = form.save(commit=False)
            employer.user = request.user
            employer.save()
            return redirect('employer_home_page')  # ✅ Redirect AFTER profile completion

    else:
        form = EmployerProfileForm(instance=employer)

    return render(request, 'employer_profile_setup.html', {'form': form})


@csrf_exempt  # Temporarily disable CSRF protection
def log_out(request):
    print("User before logout:", request.user) 
    logout(request)  
    print("User after logout:", request.user)  
    # Return response and clear CSRF cookie
    response = redirect('log-in')
    response.delete_cookie('csrftoken')
    return response


def job_matching_view(request, job_id):
    """View to match candidates to a job based on extracted skills"""
    job = get_object_or_404(Job, id=job_id)
    matched_candidates = match_candidates_to_job(job.title, top_n=5)

    if not request.user.is_authenticated:
        return redirect('log-in')

    # otherwise render
    return render(request, "candidate_matches.html", {
        "job": job,
        "matched_candidates": matched_candidates
    })



@login_required
def submit_feedback(request):
    """
    View for allowing applicants and employers to submit feedback
    """
    if request.method == 'POST':
        feedback_type = request.POST.get('feedback_type')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        priority = request.POST.get('priority', 'medium')
        
        # Validate required fields
        if not all([feedback_type, subject, message]):
            messages.error(request, "All required fields must be filled out.")
            return render(request, 'feedback_form.html')
            
        try:
            # Save feedback to database
            # Note: assuming you have a Feedback model, if not, you need to create one
            from tutorials.models.admin_models import Notification
            
            # Determine user type
            user_type = 'applicant' if hasattr(request.user, 'applicant') else 'employer'
            
            # Create notification
            notification = Notification.objects.create(
                title=f"New Feedback: {subject}",
                message=message,
                notification_type='feedback',
                priority=priority,
                sender=request.user,
                is_read=False,
                action_url=None,
                feedback_type=feedback_type,
                sender_type=user_type
            )
            
            # Don't use messages framework here to avoid it appearing in other pages
            # Instead, pass the success message directly to the template
            return render(request, 'feedback_form.html', {
                'success_message': 'Thank you for your feedback! We will process it as soon as possible.'
            })
            
        except Exception as e:
            print(f"Error saving feedback: {str(e)}")
            messages.error(request, f"Error submitting feedback: {str(e)}")
            
    return render(request, 'feedback_form.html')
