from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('verify/', views.verify_otp_view, name='verify_otp'),
    path('login/', views.login_view, name='login'),
]
