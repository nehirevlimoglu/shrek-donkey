from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse  # Used for redirection
from django.contrib.auth.decorators import login_required
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
    
    # Render login page and force set new CSRF cookie
    response = render(request, 'log_in.html')
    response.set_cookie('csrftoken', request.META.get('CSRF_COOKIE', ''), samesite=None)
    return response


@ensure_csrf_cookie
def log_in(request):
    # Clear any feedback messages before rendering login page
    
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
            messages.error(request, "Incorrect username or password", extra_tags="login")
    
    # Force set CSRF Cookie
    response = render(request, 'log_in.html')
    response.set_cookie('csrftoken', request.META.get('CSRF_COOKIE', ''), samesite='Lax')
    return response


@login_required
def applicant_profile_setup(request):
    print("🔍 Checking if user is an applicant...")
    try:
        applicant = request.user.applicant
    except Applicant.DoesNotExist:
        applicant = None

    if request.method == 'POST':
        print("📥 Form submission detected.")
        form = ApplicantForm(request.POST, request.FILES, user=request.user, instance=applicant)
        if form.is_valid():
            applicant = form.save(commit=False)
            applicant.user = request.user
            applicant.save()

            form.save_m2m()  # ✅ This is required for ManyToMany fields to save properly
            print("✅ Saved job preferences:", applicant.job_preferences.all())

            return redirect('applicants-home-page')
        else:
            print("❌ Form errors:", form.errors)
    else:
        form = ApplicantForm(user=request.user, instance=applicant)

    return render(request, 'applicant_profile_setup.html', {'form': form})


@login_required
def employer_profile_setup(request):
    print("📥 [DEBUG] employer_profile_setup view hit.")
    print(f"🔐 Logged-in user: {request.user.username} (ID: {request.user.id})")

    try:
        employer = request.user.employer
        print("✅ Employer object found for this user.")
    except Employer.DoesNotExist:
        employer = None
        print("⚠️ No employer object found. Will create new.")

    if request.method == 'POST':
        print("📝 POST request received.")
        print("📌 POST data:", request.POST)
        print("📎 FILES data:", request.FILES)

        form = EmployerProfileForm(request.POST, request.FILES, instance=employer)
        if form.is_valid():
            print("✅ Employer profile form is valid. Saving...")

            employer = form.save(commit=False)
            employer.user = request.user
            # Ensure the Employer's username matches the logged-in user's username.
            employer.username = request.user.username
            employer.save()

            print("📦 Employer saved. Redirecting to employer_home_page.")
            return redirect('employer_home_page')
        else:
            print("❌ Employer profile form is invalid.")
            print("🚨 Form errors:", form.errors)
    else:
        print("📄 GET request — rendering profile setup form.")
        form = EmployerProfileForm(instance=employer)

    return render(request, 'employer_profile_setup.html', {'form': form})




@csrf_exempt  # Temporarily disable CSRF protection
def log_out(request):
    print("User before logout:", request.user) 
    logout(request)  
    print("User after logout:", request.user)  
    # Return response and clear CSRF cookie
    response = redirect('log_in')
    response.delete_cookie('csrftoken')
    return response


def job_matching_view(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    matched_candidates = match_candidates_to_job(job.title, top_n=5)

    # 🔥 Add this block to prevent the template crash
    if isinstance(matched_candidates, str):  # If it's an error string
        return render(request, "candidate_matches.html", {
            "job": job,
            "error": matched_candidates
        })

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


def sign_up(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            # Immediately create profile based on role
            if user.role == 'Employer':
                Employer.objects.create(user=user, username=user.username, email=user.email)
                return redirect('employer_profile_setup')
            elif user.role == 'Applicant':
                Applicant.objects.create(user=user)
                return redirect('applicant_profile_setup')
            return redirect('log_in')
    else:
        form = SignUpForm()
    return render(request, 'sign_up.html', {'form': form})