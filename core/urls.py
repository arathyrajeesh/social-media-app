from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),  # Home page
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
    path('post/<int:post_id>/likes/', views.post_likes_view, name='post_likes'),
    path('post/edit/<int:post_id>/', views.edit_post_view, name='edit_post'),
    path('post/delete/<int:post_id>/', views.delete_post_view, name='delete_post'),
    path('post/toggle-hide/<int:post_id>/', views.toggle_hide_post_view, name='toggle_hide_post'),
    path('comment/like/<int:comment_id>/', views.like_comment, name='like_comment'),
    path('logout/', views.logout_view, name='logout'),
]
