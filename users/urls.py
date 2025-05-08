from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='users/logout.html'), name='logout'),
    path('', views.home, name='home'),
    path('profile/', views.profile, name='profile'),
    path('create_package/', views.create_package, name='create-package'),
    # path('buy_package/', views.buy_package, name='buy-package'),
    path('manage_users/', views.manage_users, name='manage-users'),
    path('set-currency/', views.set_currency, name='set_currency'),
]