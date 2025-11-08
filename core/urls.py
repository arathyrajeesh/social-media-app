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
    path('like/<int:post_id>/', views.like_post_view, name='like_post'),
    path('comment/<int:post_id>/', views.comment_post, name='comment_post'),
    path('user/<str:username>/', views.user_profile_view, name='user_profile'),
    path('user/<str:username>/follow/', views.follow_user, name='follow_user'),
    path('user/<str:username>/unfollow/', views.unfollow_user, name='unfollow_user'),

]


