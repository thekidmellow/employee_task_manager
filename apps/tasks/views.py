"""
Task management views with role-based access control
Demonstrates business logic and data manipulation (LO2)
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Task, TaskComment
from .forms import TaskCreationForm, TaskUpdateForm, TaskCommentForm
from accounts.models import UserProfile

