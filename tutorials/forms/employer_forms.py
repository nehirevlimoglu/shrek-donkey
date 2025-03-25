import os
import json
from django import forms
from tutorials.models.employer_models import Job, Interview
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from tutorials.models.employer_models import Employer, Interview
from django.conf import settings
from tutorials.utils import extract_skills_nlp



class InterviewForm(forms.ModelForm):
    class Meta:
        model = Interview
        fields = ['candidate', 'job', 'date', 'time', 'interview_link', 'notes']


def get_job_titles():
    json_path = os.path.join(settings.BASE_DIR, 'static/data/job_titles.json')
    try:
        with open(json_path, 'r') as file:
            job_titles = json.load(file)
        return [(title, title) for title in job_titles]
    except FileNotFoundError:
        return [("Other", "Other")]


class JobForm(forms.ModelForm):
    """ Job form with text inputs for title and position. """

    required_experience = forms.FloatField(
        widget=forms.HiddenInput(),
        required=False
    )

    title = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Job Title'})
    )

    position = forms.CharField(  # ✅ Ensure position is a text field
        required=False,  # Allow it to be optional
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Position'})
    )

    class Meta:
        model = Job
        fields = [
            'title', 'position', 'company_name', 'location', 'job_type',
            'salary', 'description', 'requirements', 'benefits', 'application_deadline', 'contact_email', 'required_experience'
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company Name'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Location'}),
            'job_type': forms.Select(attrs={'class': 'form-control'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Salary (optional)'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Job Description'}),
            'requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Requirements'}),
            'benefits': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Benefits (optional)'}),
            'application_deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Contact Email'}),
        }

    def save(self, commit=True):
        job = super().save(commit=False)

        # Extract skills from requirements field and save to a json field
        skills = extract_skills_nlp(job.requirements)
        print(f"Extracted skills: {skills}")
        job.extracted_skills = json.dumps(skills)

        if commit:
            job.save()

        return job

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

        
class EmployerProfileForm(forms.ModelForm):
    # Include optional user fields with Bootstrap styling
    first_name = forms.CharField(
        max_length=30,
        required=False,
        label='First Name',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        label='Last Name',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        required=False,
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )

    class Meta:
        model = Employer
        fields = [
            'company_name',
            'company_logo',
            'company_website',
            'industry',
            'company_location',
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company Name'}),
            'company_logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'company_website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://'}),
            'industry': forms.Select(attrs={'class': 'form-select'}),
            'company_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Location'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # grab the user instance if passed
        super().__init__(*args, **kwargs)

        # Pre-populate user fields if user is passed in
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email

    def save(self, commit=True):
        employer = super().save(commit=False)

        # Save related user info too
        if self.user:
            self.user.first_name = self.cleaned_data.get('first_name', self.user.first_name)
            self.user.last_name = self.cleaned_data.get('last_name', self.user.last_name)
            self.user.email = self.cleaned_data.get('email', self.user.email)
            if commit:
                self.user.save()

        if commit:
            employer.save()
            self.save_m2m()

        return employer

class RescheduleInterviewForm(forms.ModelForm):
    class Meta:
        model = Interview
        fields = ['date', 'time', 'interview_link', 'notes']  # which fields to edit
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
        }