from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from .models import UserProfile

User = get_user_model()


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        })
    )

    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        required=False,  # <- made optional
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='Select your role in the organization (optional)'
    )
    department = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your department (optional)'
        })
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your phone number (optional)'
        })
    )

    class Meta:
        model = User

        fields = ('username', 'first_name', 'last_name',
                  'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choose a username'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter a strong password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })

    def clean_email(self):

        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email

    def clean_username(self):

        username = self.cleaned_data.get('username') or ""
        if len(username) < 3:
            raise ValidationError(
                "Username must be at least 3 characters long.")
        # Allow letters, numbers, underscores and hyphens
        allowed = username.replace('_', '').replace('-', '')
        if not allowed.isalnum():
            raise ValidationError(
                "Username can only contain letters, numbers, hyphens, and underscores.")
        return username

    def save(self, commit=True):

        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email', '')
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')

        if commit:
            user.save()

            profile, _ = UserProfile.objects.get_or_create(user=user)
            role = self.cleaned_data.get('role')
            if role:
                profile.role = role
            department = self.cleaned_data.get('department')
            if department:
                profile.department = department
            phone = self.cleaned_data.get('phone_number')
            if phone:
                profile.phone_number = phone
            profile.save()

        return user


class UserProfileForm(forms.ModelForm):

    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        })
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )

    class Meta:
        model = UserProfile
        fields = ['phone_number', 'department']
        widgets = {
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your phone number'
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your department'
            }),
        }

    def clean_phone_number(self):

        phone = self.cleaned_data.get('phone_number')
        if phone:
            digits_only = ''.join(filter(str.isdigit, phone))
            if len(digits_only) < 10 or len(digits_only) > 15:
                raise ValidationError(
                    "Phone number must be between 10 and 15 digits.")
        return phone
