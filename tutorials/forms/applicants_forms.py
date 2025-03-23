# tutorials/forms/applicants_forms.py

from django import forms
from tutorials.models.applicants_models import Applicant, Application, JobTitle
from tutorials.models.employer_models import JobTitle
from django.core.exceptions import ValidationError

class ApplicantForm(forms.ModelForm):
    DEGREE_CHOICES = [
        ('', 'Select Degree'),
        ('bachelors', 'Bachelors'),
        ('masters', 'Masters'),
        ('phd', 'PhD'),
        ('diploma', 'Diploma'),
        ('associate', 'Associate Degree'),
        ('certificate', 'Certificate'),
    ]

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
    degree = forms.ChoiceField(
        choices=DEGREE_CHOICES,
        required=True,
        widget=forms.Select(attrs={"class": "form-control"})
    )
    job_preferences = forms.ModelMultipleChoiceField(
        queryset=JobTitle.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        required=False
    )

    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    ALLOWED_FILE_TYPES = ['application/pdf', 'application/msword', 
                         'application/vnd.openxmlformats-officedocument.wordprocessingml.document']

    def clean_cv(self):
        cv = self.cleaned_data.get('cv')
        if cv:
            if cv.size > self.MAX_FILE_SIZE:
                raise forms.ValidationError('File size must be under 5MB')
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
            "salary_preferences": forms.TextInput(attrs={"class": "form-control"}),
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

        if applicant.user:
            user = applicant.user
            user.first_name = self.cleaned_data["first_name"]
            user.last_name = self.cleaned_data["last_name"]
            if commit:
                user.save()

        if commit:
            applicant.save()
            self.save_m2m()  # ✅ This is what actually saves job_preferences

        return applicant





# ✅ Custom validator to enforce PDF file uploads only
def validate_pdf(value):
    if not value.name.endswith(".pdf"):
        raise ValidationError("❌ Only PDF files are allowed for resumes!")
        

class ApplicationForm(forms.ModelForm):
    # Personal Information
    first_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={"class": "form-control"}))
    last_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={"class": "form-control"}))
    phone = forms.CharField(max_length=20, required=True, widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"class": "form-control"}))
    address = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={"class": "form-control"}))

    # Resume & Cover Letter
    resume = forms.FileField(
        required=True, 
        widget=forms.FileInput(attrs={"class": "form-control"}), 
        validators=[validate_pdf]
    )
    
    cover_letter = forms.FileField(
        required=False, 
        widget=forms.FileInput(attrs={"class": "form-control"}), 
        validators=[validate_pdf]
    )

    # Education
    school = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    degree = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    
    DISCIPLINE_CHOICES = [
        ('bachelors', 'Bachelors'),
        ('masters', 'Masters'),
        ('phd', 'PhD'),
        ('diploma', 'Diploma'),
        ('associate', 'Associate Degree'),
        ('certificate', 'Certificate'),
    ]
    discipline = forms.ChoiceField(
        choices=DISCIPLINE_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-control"})
    )

    start_date = forms.DateField(required=False, widget=forms.SelectDateWidget(years=range(1980, 2030)))
    end_date = forms.DateField(required=False, widget=forms.SelectDateWidget(years=range(1980, 2030)))

    # 🔥 Work Experience (INDIVIDUAL FIELDS)
    work_job_title = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    work_employer = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    work_start_date = forms.DateField(required=False, widget=forms.SelectDateWidget(years=range(1980, 2030)))
    work_end_date = forms.DateField(required=False, widget=forms.SelectDateWidget(years=range(1980, 2030)))
    job_description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 4})
    )

    # Current Job
    current_job_title = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    current_employer = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    linkedin_profile = forms.URLField(required=False, widget=forms.URLInput(attrs={"class": "form-control"}))
    portfolio_website = forms.URLField(required=False, widget=forms.URLInput(attrs={"class": "form-control"}))

    # Skills and Extra
    skills = forms.CharField(
        max_length=500, 
        required=False, 
        widget=forms.TextInput(attrs={
            "class": "form-control", 
            "placeholder": "Enter skills separated by commas (e.g., Python, Django, Machine Learning)"
        })
    )

    how_did_you_hear = forms.ChoiceField(
        choices=[("linkedin", "LinkedIn"), ("website", "Company Website"), ("referral", "Referral"), ("other", "Other")],
        required=True, widget=forms.Select(attrs={"class": "form-control"})
    )

    sponsorship_needed = forms.ChoiceField(
        choices=[("yes", "Yes"), ("no", "No")], 
        required=True, 
        widget=forms.Select(attrs={"class": "form-control"})
    )

    confirm_information = forms.BooleanField(
        required=True, 
        label="I confirm all information is accurate.", 
        widget=forms.CheckboxInput()
    )

    class Meta:
        model = Application
        fields = [
            "first_name", "last_name", "email", "phone", "address", "resume", "cover_letter",
            "skills",
            "school", "degree", "discipline", "start_date", "end_date",
            "work_job_title", "work_employer", "work_start_date", "work_end_date", "job_description",  # ✅ Added fields
            "current_job_title", "current_employer", "linkedin_profile", "portfolio_website",
            "how_did_you_hear", "sponsorship_needed", "confirm_information",
        ]
