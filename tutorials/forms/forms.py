from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm

class SignUpForm(forms.ModelForm):

    ROLE_CHOICES=[
        ('Employer', 'Employer'), ('Applicant', 'Applicant'), ('Admin', 'Admin')
    ]

    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        required=True,
        label="Role",
        widget=forms.Select(attrs={'class': 'form-control'}) 
    )

    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'role']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")
        return password2

    def save(self, commit=True):
        """Save the user with the selected role"""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data.get('password1'))
        user.role = self.cleaned_data['role']
        if commit:
            user.save()
        return user

class LogInForm(AuthenticationForm):
    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your username'
        })
    )

    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )