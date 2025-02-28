# tutorials/forms/applicants_forms.py

from django import forms
from tutorials.models.applicants_models import Applicant

class ApplicantForm(forms.ModelForm):
    first_name = forms.CharField(
        label="First Name",
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    last_name = forms.CharField(
        label="Last Name",
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    ALLOWED_FILE_TYPES = ['application/pdf', 'application/msword', 
                         'application/vnd.openxmlformats-officedocument.wordprocessingml.document']

    def clean_cv(self):
        cv = self.cleaned_data.get('cv')
        if cv:
            # Check file size
            if cv.size > self.MAX_FILE_SIZE:
                raise forms.ValidationError('File size must be under 5MB')
            
            # Check file type
            if hasattr(cv, 'content_type') and cv.content_type not in self.ALLOWED_FILE_TYPES:
                raise forms.ValidationError('Only PDF and Word documents are allowed')
        return cv

    min_salary_preference = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 50000',
                'min': '0',
                'step': '1000'
            }
        ),
        help_text="Enter your minimum expected annual salary"
    )
    
    max_salary_preference = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 70000',
                'min': '0',
                'step': '1000'
            }
        ),
        help_text="Enter your maximum expected annual salary"
    )

    def clean(self):
        cleaned_data = super().clean()
        min_salary = cleaned_data.get('min_salary_preference')
        max_salary = cleaned_data.get('max_salary_preference')

        if min_salary and max_salary and min_salary > max_salary:
            # Swap the values if min is greater than max
            cleaned_data['min_salary_preference'] = max_salary
            cleaned_data['max_salary_preference'] = min_salary

        return cleaned_data

    class Meta:
        model = Applicant
        fields = [
            "degree",
            "cv",
            "min_salary_preference",
            "max_salary_preference",
            "job_preferences",
            "location_preferences",
        ]
        widgets = {
            "degree": forms.TextInput(attrs={"class": "form-control"}),
            "min_salary_preference": forms.TextInput(attrs={"class": "form-control"}),
            "max_salary_preference": forms.TextInput(attrs={"class": "form-control"}),
            "job_preferences": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "location_preferences": forms.TextInput(attrs={"class": "form-control"}),
            "cv": forms.FileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            # Prepopulate first_name and last_name from the User model
            self.fields["first_name"].initial = user.first_name
            self.fields["last_name"].initial = user.last_name

    def save(self, commit=True):
        applicant = super().save(commit=False)
        
        # Ensure that the user is saved along with the applicant details
        if applicant.user:
            user = applicant.user
            user.first_name = self.cleaned_data["first_name"]
            user.last_name = self.cleaned_data["last_name"]
            if commit:
                user.save()  # Save the updated User model

        if commit:
            applicant.save()  # Save the Applicant model

        return applicant
