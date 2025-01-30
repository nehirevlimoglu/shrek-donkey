from django import forms
from tutorials.models.applicants_models import Applicant

class ApplicantForm(forms.ModelForm):
    class Meta:
        model = Applicant
        fields = ['degree', 'cv', 'salary_preferences', 'job_preferences', 'location_preferences']
        widgets = {
            'job_preferences': forms.Textarea(attrs={'rows': 3}),
        }
