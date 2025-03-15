# tutorials/forms/applicants_forms.py

from django import forms
from tutorials.models.applicants_models import Applicant, Application
from tutorials.models.employer_models import JobTitle


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
    job_preferences = forms.ModelMultipleChoiceField(
        queryset=JobTitle.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
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
    


class ApplicationForm(forms.ModelForm):
    # Personal Information
    first_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={"class": "form-control"}))
    last_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={"class": "form-control"}))
    phone = forms.CharField(max_length=20, required=True, widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"class": "form-control"}))
    address = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={"class": "form-control"}))

    # Resume & Cover Letter
    resume = forms.FileField(required=True, widget=forms.FileInput(attrs={"class": "form-control"}))
    cover_letter = forms.FileField(required=False, widget=forms.FileInput(attrs={"class": "form-control"}))

    # ✅ Make Education Fields Optional (Fix for blocking issue)
    school = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    degree = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    discipline = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    start_date = forms.DateField(widget=forms.SelectDateWidget(years=range(1980, 2030)), required=False)
    end_date = forms.DateField(widget=forms.SelectDateWidget(years=range(1980, 2030)), required=False)

    # ✅ Keep Other Fields the Same
    current_job_title = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    current_employer = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    linkedin_profile = forms.URLField(required=False, widget=forms.URLInput(attrs={"class": "form-control"}))
    portfolio_website = forms.URLField(required=False, widget=forms.URLInput(attrs={"class": "form-control"}))

    how_did_you_hear = forms.ChoiceField(
        choices=[("linkedin", "LinkedIn"), ("website", "Company Website"), ("referral", "Referral"), ("other", "Other")],
        required=True, widget=forms.Select(attrs={"class": "form-control"})
    )

    sponsorship_needed = forms.ChoiceField(choices=[("yes", "Yes"), ("no", "No")], required=True, widget=forms.Select(attrs={"class": "form-control"}))

    confirm_information = forms.BooleanField(required=True, label="I confirm all information is accurate.", widget=forms.CheckboxInput())

    class Meta:
        model = Application
        fields = [
            "first_name", "last_name", "email", "phone", "address", "resume", "cover_letter",
            "school", "degree", "discipline", "start_date", "end_date",  # ✅ Education is now optional
            "current_job_title", "current_employer", "linkedin_profile", "portfolio_website",
            "how_did_you_hear", "sponsorship_needed", "confirm_information",
        ]
