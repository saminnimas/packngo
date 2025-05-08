from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.urls import reverse

from .models import CustomUser
from notifications.models import Notification
from packages.models import Package
from .forms import UserRegisterForm, UserProfileForm
from packages.forms import PackageForm
from .utils import convert_currency, get_currency_symbol


def is_admin(user) -> bool:
    return user.is_staff


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False) # save user to database; 
            user.is_staff = False # also ensuring that new users ain't getting admin privilidges
            user.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('home')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})


def home(request):
    packages = Package.objects.filter(is_available=True)
    
    currency = request.session.get('currency', 'BDT')
    
    for package in packages:
        package.converted_price = convert_currency(package.price, to_currency=currency)
        package.currency_symbol = get_currency_symbol(currency)
    
    context = {
        'packages': packages,
        'selected_currency': currency,
    }
    return render(request, 'users/home.html', context)


@login_required
@user_passes_test(is_admin)
def create_package(request):
    if request.method == 'POST':
        package_form = PackageForm(request.POST, request.FILES)
        if package_form.is_valid():
            package = package_form.save(commit=False)
            package.created_by = request.user
            package.save()
            messages.success(request, 'Package created!!')
            User = get_user_model()
            for user in User.objects.filter(is_staff=False):
                Notification.objects.create(
                    user=user,
                    notification_type='new_package',
                    message=f"New package '{package.package_name}' is available!",
                    package=package
                )
            return redirect('home')
    else:
        package_form = PackageForm()
    return render(request, 'users/create_package.html', {'form': package_form})


@login_required
@user_passes_test(is_admin)
def manage_users(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        try:
            user = CustomUser.objects.get(id=user_id)
            if action == 'grant_admin':
                user.is_staff = True
                user.save()
                messages.success(request, f"Admin access granted to {user.username}!")
            elif action == 'revoke_admin':
                if user != request.user:
                    if user.is_superuser:
                        messages.error(request, "CANNOT REVOKE SUPERUSER'S ADMIN ACCESS. HOW DARE YOU!!")
                    else:
                        user.is_staff = False
                        user.save()
                        messages.success(request, f"Admin access revoked from {user.username}")
                elif user == request.user:
                    messages.error(request, "CANNOT REVOKE YOUR OWN ADMIN ACCESS. GET SOME HELP!!")
        except CustomUser.DoesNotExist:
            messages.error(request, "User not found.")
        

    users = CustomUser.objects.all()
    return render(request, 'users/manage_users.html', {'users': users}) # NO REDIRECTION REQUIRED; MESSAGES WILL APPEAR IN THIS PAGE


# @login_required
# def buy_package(request):
#     packages = Package.objects.filter(is_custom = False)
#     return render(request, 'users/buy_package.html', {'packages': packages})


@login_required
def profile(request):
    if request.method == 'POST':
        profile_form = UserProfileForm(request.POST, instance=request.user)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Profile Updated Sucessfully!')
            Notification.objects.create(
            user=request.user,
            notification_type='profile_update',
            message="You updated your profile."
            )
            return redirect('profile')
        else:
            messages.error(request, 'Error updating profile. Make sure your input/s are correct.')
            print("Form Errors:", profile_form.errors)
    else:
        profile_form = UserProfileForm(instance=request.user)
    return render(request, 'users/profile.html', {'form': profile_form})


def set_currency(request):
    """Set the user's preferred currency in the session."""
    if request.method == 'POST':
        currency = request.POST.get('currency', 'BDT')
        if currency in ['BDT', 'USD', 'EUR', 'SAR', 'JPY']:
            request.session['currency'] = currency
    return redirect(request.META.get('HTTP_REFERER', reverse('home')))