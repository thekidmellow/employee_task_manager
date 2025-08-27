"""
User authentication and profile forms
Demonstrates form validation and user input handling (LO2.4)
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import UserProfile
