import os
import json
from django import forms
from tutorials.models.employer_models import Job, Interview
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from tutorials.models.employer_models import Employer
from django.conf import settings




class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'description', 'requirements', 'salary', 'job_type']

class InterviewForm(forms.ModelForm):
    class Meta:
        model = Interview
        fields = ['candidate', 'job', 'date', 'time', 'interview_link', 'notes']


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


def get_job_titles():
    json_path = os.path.join(settings.BASE_DIR, 'static/data/job_titles.json')
    try:
        with open(json_path, 'r') as file:
            job_titles = json.load(file)
        return [(title, title) for title in job_titles]
    except FileNotFoundError:
        return [("Other", "Other")]

class JobForm(forms.ModelForm):
    position = forms.ChoiceField(
        choices=get_job_titles(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Job
        fields = [
            'title', 'position', 'company_name', 'location', 'job_type',
            'salary', 'description', 'requirements', 'benefits', 'application_deadline', 'contact_email'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Job Title'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company Name'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Location'}),
            'job_type': forms.Select(attrs={'class': 'form-control'}),
            'salary': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Salary (optional)'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Job Description'}),
            'requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Requirements'}),
            'benefits': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Benefits (optional)'}),
            'application_deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Contact Email'}),
        }


class EmployerProfileForm(forms.ModelForm):
    class Meta:
        model = Employer
        fields = ['company_name', 'company_logo', 'company_website', 'industry', 'company_location']