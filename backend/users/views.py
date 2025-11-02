from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm

from .forms import SignupForm


@require_http_methods(["GET", "POST"])
def signup_view(request):
    """
    Signup view that creates a user, tenant organization, and profile.
    After successful signup, user is automatically logged in.
    """
    if request.user.is_authenticated:
        messages.info(request, "You are already logged in.")
        return redirect('users:profile')
    
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in automatically
            login(request, user)
            messages.success(
                request,
                f"Welcome! Your account and organization '{user.profile.tenant.name}' have been created successfully."
            )
            return redirect('users:profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = SignupForm()
    
    return render(request, 'users/signup.html', {'form': form})


@login_required
def profile_view(request):
    """View current user's profile"""
    try:
        profile = request.user.profile
        return render(request, 'users/profile.html', {
            'profile': profile,
            'user': request.user,
            'tenant': profile.tenant
        })
    except AttributeError:
        messages.warning(request, "You don't have a profile yet. Please contact an administrator.")
        return redirect('admin:index')


def home_view(request):
    """Home page view"""
    return render(request, 'users/home.html')


@require_http_methods(["GET", "POST"])
def login_view(request):
    """Custom login view"""
    if request.user.is_authenticated:
        messages.info(request, "You are already logged in.")
        return redirect('users:profile')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                next_url = request.GET.get('next', 'users:profile')
                return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    
    return render(request, 'users/login.html', {'form': form})
