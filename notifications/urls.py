from django.urls import path
from . import views

urlpatterns = [
    path('', views.notifications_list, name='notifications_list'),
    path('<int:notification_id>/', views.notification_redirect, name='notification_redirect'),
]