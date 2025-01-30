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

    class Meta:
        model = Applicant
        fields = [
            "degree",
            "cv",
            "salary_preferences",
            "job_preferences",
            "location_preferences",
        ]
        widgets = {
            "degree": forms.TextInput(attrs={"class": "form-control"}),
            "salary_preferences": forms.TextInput(attrs={"class": "form-control"}),
            "job_preferences": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "location_preferences": forms.TextInput(attrs={"class": "form-control"}),
            "cv": forms.FileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields["first_name"].initial = user.first_name
            self.fields["last_name"].initial = user.last_name

    def save(self, commit=True):
        applicant = super().save(commit=False)
        user = self.instance.user
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
            applicant.save()
        return applicant