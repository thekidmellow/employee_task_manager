"""
User authentication and profile forms
Demonstrates form validation and user input handling (LO2.4)
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import UserProfile


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control','placeholder': 'Enter your email address'})
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control','placeholder': 'Enter your first name'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control','placeholder': 'Enter your last name'})
    )
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='Select your role in the organization'
    )
    department = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control','placeholder': 'Enter your department (optional)'})
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control','placeholder': 'Enter your phone number (optional)'})
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control','placeholder': 'Choose a username'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control','placeholder': 'Enter a strong password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control','placeholder': 'Confirm your password'})
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            if User.objects.filter(email=email).exists():
                raise ValidationError("A user with this email already exists.")
            if not email.endswith(('@company.com', '@gmail.com', '@yahoo.com', '@outlook.com')):
                raise ValidationError("Please use a valid email domain.")
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            if len(username) < 3:
                raise ValidationError("Username must be at least 3 characters long.")
            if not username.replace('_', '').replace('-', '').isalnum():
                raise ValidationError("Username can only contain letters, numbers, hyphens, and underscores.")
        return username

    class UserProfileForm(forms.ModelForm):
        first_name = forms.CharField(
            max_length=30,
            required=False,
            widget=forms.TextInput(attrs={'class': 'form-control','placeholder': 'Enter your first name'})
        )
        last_name = forms.CharField(
            max_length=30,
            required=False,
            widget=forms.TextInput(attrs={'class': 'form-control','placeholder': 'Enter your last name'})
        )
        email = forms.EmailField(
            required=False,
            widget=forms.EmailInput(attrs={'class': 'form-control','placeholder': 'Enter your email address'})
        )
    
        class Meta:
            model = UserProfile
            fields = ['phone_number', 'department']
            widgets = {
                'phone_number': forms.TextInput(attrs={'class': 'form-control','placeholder': 'Enter your phone number'}),
                'department': forms.TextInput(attrs={'class': 'form-control','placeholder': 'Enter your department'}),
            } 
