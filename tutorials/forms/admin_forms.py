from django import forms
from tutorials.models.admin_models import Admin

class AdminProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=False, label='First Name')
    last_name = forms.CharField(max_length=150, required=False, label='Last Name')
    email = forms.EmailField(required=False, label='Email')

    class Meta:
        model = Admin
        fields = ['phone_number']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email

    def save(self, commit=True):
        admin = super().save(commit=False)

        # Save related User fields too
        if self.user:
            self.user.first_name = self.cleaned_data.get('first_name')
            self.user.last_name = self.cleaned_data.get('last_name')
            self.user.email = self.cleaned_data.get('email')
            if commit:
                self.user.save()

        if commit:
            admin.save()

        return admin


class AdminProfileForm(forms.ModelForm):
    # Optional user fields (linked via OneToOne)
    first_name = forms.CharField(
        max_length=150,
        required=False,
        label='First Name',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=150,
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
        model = Admin
        fields = [
            'phone_number',
        ]
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1234567890'})
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # Grab the user instance if passed
        super().__init__(*args, **kwargs)

        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email

    def save(self, commit=True):
        admin = super().save(commit=False)

        if self.user:
            self.user.first_name = self.cleaned_data.get('first_name', self.user.first_name)
            self.user.last_name = self.cleaned_data.get('last_name', self.user.last_name)
            self.user.email = self.cleaned_data.get('email', self.user.email)
            if commit:
                self.user.save()

        if commit:
            admin.save()

        return admin