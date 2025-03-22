from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse  # Used for redirection
from django.contrib.auth.decorators import login_required
from tutorials.helpers import login_prohibited, clear_feedback_messages  # If used elsewhere
from tutorials.forms.applicants_forms import ApplicantForm  # Applicant profile form
from tutorials.forms.employer_forms import EmployerProfileForm  # Employer profile form
from tutorials.models.applicants_models import Applicant  # Applicant model
from tutorials.models.employer_models import Employer  # Employer model
from tutorials.models.user_model import User

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm

User = get_user_model()  # Using your custom User model

# --------------------
#       VIEWS
# --------------------

def log_in(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        print(f"Attempting login: {username} | {password}")  # Debug output
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            print(f"User authenticated: {user.username} | Role: {user.role}")  # Debug output
            login(request, user)
            # Redirect based on role
            if request.user.role == 'Admin':
                return redirect('admin_home_page')
            elif request.user.role == 'Employer':
                return redirect('employer_home_page')
            elif request.user.role in ['Applicant', 'job_seeker']:
                return redirect('applicants-home-page')
            raise Http404("Page not found")
        else:
            print("Authentication failed")
            # Optionally add a message or redirect back with an error.
    
    # Clear any feedback messages before rendering login page
    clear_feedback_messages(request)
    
    return render(request, 'log_in.html')


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
            return redirect('applicants-home-page')
    else:
        form = ApplicantForm(user=request.user, instance=applicant)
    return render(request, 'applicant_profile_setup.html', {'form': form})






def log_out(request):
    print("User before logout:", request.user)
    logout(request)
    print("User after logout:", request.user)
    return redirect('log-in')


# --------------------
#       FORMS
# --------------------

class SignUpForm(forms.ModelForm):
    ROLE_CHOICES = [
        ('Employer', 'Employer'),
        ('Applicant', 'Applicant'),
    ]

    first_name = forms.CharField(
        label="First Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
        required=True
    )
    last_name = forms.CharField(
        label="Last Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
        required=True
    )
    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'}),
        required=True
    )
    confirm_email = forms.EmailField(
        label="Confirm Email",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Confirm your email'}),
        required=True
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your password'}),
        required=True
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm your password'}),
        required=True
    )
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        required=True,
        label="Role",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'role']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your username'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        confirm_email = cleaned_data.get("confirm_email")
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if email and confirm_email and email != confirm_email:
            self.add_error('confirm_email', "Email addresses do not match.")
        if password1 and password2 and password1 != password2:
            self.add_error('password2', "Passwords do not match.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        # Use Django's set_password to hash the password correctly
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class LogInForm(AuthenticationForm):
    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your username'})
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your password'})
    )


class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Old Password'}),
        label="Old Password"
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New Password'}),
        label="New Password"
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm New Password'}),
        label="Confirm New Password"
    )

    class Meta:
        model = User
        fields = ['old_password', 'new_password1', 'new_password2']
