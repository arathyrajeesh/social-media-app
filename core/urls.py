from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('verify/', views.verify_otp_view, name='verify_otp'),
    path('resend/', views.resend_otp_view, name='resend_otp'),
    path('login/', views.login_view, name='login'),
    path('forgot/', views.forgot_password_view, name='forgot_password'),
    path('reset/', views.reset_password_view, name='reset_password'),
    path('feed/', views.feed_view, name='feed'),
    path('create/', views.create_post_view, name='create_post'),
]


