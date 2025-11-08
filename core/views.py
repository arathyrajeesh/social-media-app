import random
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from .forms import RegisterForm,PostForm
from .models import Profile,Post,Like,Follow,Comment
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            otp = str(random.randint(100000, 999999))
            profile = Profile.objects.get(user=user)
            profile.otp = otp
            profile.save()

            send_mail(
                'Your OTP for Verification',
                f'Hello {user.username},\n\nYour OTP is {otp}.',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            request.session['email'] = user.email
            return redirect('verify_otp')
    else:
        form = RegisterForm()
    return render(request, 'core/register.html', {'form': form})


def verify_otp_view(request):
    email = request.session.get('email')
    if not email:
        return redirect('register')

    user = User.objects.get(email=email)
    profile = Profile.objects.get(user=user)

    if request.method == 'POST':
        otp = request.POST.get('otp')
        if otp == profile.otp:
            profile.is_verified = True
            profile.otp = ''
            profile.save()
            return redirect('login')
        else:
            return render(request, 'core/verify_otp.html', {'error': 'Invalid OTP'})

    return render(request, 'core/verify_otp.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)
        if user is not None:
            profile = Profile.objects.get(user=user)
            if profile.is_verified:
                login(request, user)
                return redirect('feed')  # ✅ Go to feed after successful login
            else:
                return render(request, 'core/login.html', {'error': 'Please verify your email first'})
        else:
            return render(request, 'core/login.html', {'error': 'Invalid credentials'})

    return render(request, 'core/login.html')

def resend_otp_view(request):
    email = request.session.get('email')
    if not email:
        return redirect('register')

    user = User.objects.get(email=email)
    profile = Profile.objects.get(user=user)

    # Generate a new OTP
    otp = str(random.randint(100000, 999999))
    profile.otp = otp
    profile.save()

    # Send new OTP email
    send_mail(
        'Your New OTP for Verification',
        f'Hello {user.username},\n\nYour new OTP is {otp}.',
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )

    return render(request, 'core/verify_otp.html', {
        'email': email,
        'message': 'A new OTP has been sent to your email.'
    })

def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            profile = Profile.objects.get(user=user)

            otp = str(random.randint(100000, 999999))
            profile.otp = otp
            profile.save()

            send_mail(
                'Password Reset OTP',
                f'Hi {user.username},\n\nYour password reset OTP is {otp}.',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )

            request.session['reset_email'] = email
            return redirect('reset_password')
        except User.DoesNotExist:
            return render(request, 'core/forgot_password.html', {'error': 'Email not found'})
    return render(request, 'core/forgot_password.html')


def reset_password_view(request):
    email = request.session.get('reset_email')
    if not email:
        return redirect('forgot_password')

    user = User.objects.get(email=email)
    profile = Profile.objects.get(user=user)

    if request.method == 'POST':
        otp = request.POST.get('otp')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if otp != profile.otp:
            return render(request, 'core/reset_password.html', {'error': 'Invalid OTP'})

        if new_password != confirm_password:
            return render(request, 'core/reset_password.html', {'error': 'Passwords do not match'})

        user.set_password(new_password)
        user.save()
        profile.otp = ''
        profile.save()

        messages.success(request, 'Password reset successful! You can now log in.')
        return redirect('login')

    return render(request, 'core/reset_password.html')

@login_required
def create_post_view(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            return redirect('feed')
    else:
        form = PostForm()
    return render(request, 'core/create_post.html', {'form': form})


@login_required
def like_post_view(request, post_id):
    post = Post.objects.get(id=post_id)
    like, created = Like.objects.get_or_create(post=post, user=request.user)
    if not created:
        # If already liked, unlike it
        like.delete()
    return HttpResponseRedirect(reverse('feed'))

@login_required
def comment_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Comment.objects.create(post=post, user=request.user, content=content)
    return redirect('feed')


@login_required
def follow_user(request, username):
    user_to_follow = get_object_or_404(User, username=username)
    if user_to_follow != request.user:
        Follow.objects.get_or_create(follower=request.user, following=user_to_follow)
    return redirect('user_profile', username=username)

@login_required
def unfollow_user(request, username):
    user_to_unfollow = get_object_or_404(User, username=username)
    Follow.objects.filter(follower=request.user, following=user_to_unfollow).delete()
    return redirect('user_profile', username=username)


@login_required
def feed_view(request):
    # Get all posts except the logged-in user's posts
    posts = Post.objects.exclude(user=request.user).order_by('-created_at')

    liked_posts = Like.objects.filter(user=request.user).values_list('post_id', flat=True)
    
    # Preload likes for each post to reduce queries
    posts_data = []
    for post in posts:
        likes = Like.objects.filter(post=post).select_related('user')
        posts_data.append({
            'post': post,
            'likes': [like.user for like in likes],
        })
    
    return render(request, 'core/feed.html', {
        'posts_data': posts_data,
        'liked_posts': liked_posts,
    })

@login_required
def user_profile_view(request, username):
    # Show the user's own posts (if viewing your own profile or someone else’s)
    profile_user = get_object_or_404(User, username=username)
    posts = Post.objects.filter(user=profile_user).order_by('-created_at')

    # Check if the logged-in user follows this profile
    is_following = Follow.objects.filter(follower=request.user, following=profile_user).exists()

    return render(request, 'core/profile.html', {
        'profile_user': profile_user,
        'posts': posts,
        'is_following': is_following,
    })


def post_likes_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    liked_users = post.likes.all()  # Assuming Post model has a ManyToManyField for likes
    return render(request, 'core/post_likes.html', {'post': post, 'liked_users': liked_users})

