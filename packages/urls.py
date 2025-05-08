from django.urls import path
from .src_views import hotel_booking
from django.shortcuts import render
from . import views

urlpatterns = [
    path('packages/', views.package_list, name='package_list'),
    path('packages/buy/<int:package_id>/', views.buy_package, name='buy_package'),
    # path('packages/<int:pk>/', views.package_detail, name='package-details'),
    
    # stand-alone urls
    path('hotels/', hotel_booking, name='hotel_booking'),
    path('flights/', views.flight_booking, name='flight_booking'),
    path('flights/get-price/', views.get_flight_price, name='get_flight_price'), # AJAX endpoint
    
    path('custom/', views.create_custom_package, name='create_custom_package'),
    path('detail/<int:package_id>/', views.package_detail, name='package_detail'),

    path('payment/gateway/<int:payment_id>/<int:package_id>', views.payment_gateway, name='payment_gateway'),
    path('payment/success/<int:payment_id>/', views.payment_success, name='payment_success'),
    path('payment/cancel/', views.payment_cancel, name='payment_cancel'),

    path('expense-log/', views.expense_log, name='expense_log'),
    path('expense-log-visualization/', views.expense_log_visualization, name='expense_log_visualization'),

    path('api/packages/<int:pk>/', views.package_detail_api, name='package_detail_api'),
    path('api/user-recommendations/', views.user_recommended_packages, name='user_recommended_packages'),
    path('api/trending-packages/', views.trending_packages, name='trending_packages'),
]