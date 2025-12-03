import random
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from .forms import RegisterForm,PostForm
from .models import Profile,Post,Like,Follow,Comment,Message,SavedPost
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render, redirect
from django.db.models import Q


def home_view(request):
    posts = Post.objects.all().order_by('-created_at')
    posts_data = []

    # Get liked posts only if user is logged in
    liked_posts = []
    if request.user.is_authenticated:
        liked_posts = Like.objects.filter(user=request.user).values_list('post_id', flat=True)

    for post in posts:
        likes = [like.user for like in Like.objects.filter(post=post)]
        posts_data.append({'post': post, 'likes': likes})

    return render(request, 'core/home.html', {
        'posts_data': posts_data,
        'liked_posts': liked_posts,
    })


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
                messages.success(request, f'Welcome back, {user.username}!')
                return redirect('feed')
            else:
                return render(request, 'core/login.html', {'error': 'Please verify your email first'})
        else:
            return render(request, 'core/login.html', {'error': 'Invalid credentials'})
    return render(request, 'core/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

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



def post_likes_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    liked_users = post.likes.all()  # Assuming Post model has a ManyToManyField for likes
    return render(request, 'core/post_likes.html', {'post': post, 'liked_users': liked_users})


@login_required
def edit_post_view(request, post_id):
    post = get_object_or_404(Post, id=post_id, user=request.user)
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('user_profile', username=request.user.username)
    else:
        form = PostForm(instance=post)
    return render(request, 'core/edit_post.html', {'form': form})

@login_required
def delete_post_view(request, post_id):
    post = get_object_or_404(Post, id=post_id, user=request.user)
    post.delete()
    return redirect('user_profile', username=request.user.username)

@login_required
def toggle_hide_post_view(request, post_id):
    post = get_object_or_404(Post, id=post_id, user=request.user)
    post.hidden = not post.hidden
    post.save()
    return redirect('user_profile', username=request.user.username)

@login_required
def comment_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        content = request.POST.get('content')
        parent_id = request.POST.get('parent_id')
        parent_comment = None
        if parent_id:
            parent_comment = Comment.objects.get(id=parent_id)
        if content:
            Comment.objects.create(post=post, user=request.user, content=content, parent=parent_comment)
    return redirect('user_profile', username=post.user.username)


@login_required
def like_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user in comment.liked_by.all():
        comment.liked_by.remove(request.user)
    else:
        comment.liked_by.add(request.user)
    return redirect('user_profile', username=comment.post.user.username)


@login_required
def feed_view(request):
    # Get users that the current user is following
    following_users = Follow.objects.filter(follower=request.user).values_list('following', flat=True)

    # Show posts only from followed users, exclude hidden posts and own posts
    posts = Post.objects.filter(
        user__in=following_users,
        hidden=False
    ).exclude(user=request.user).order_by('-created_at')

    liked_posts = Like.objects.filter(user=request.user).values_list('post_id', flat=True)
    saved_posts = SavedPost.objects.filter(user=request.user).values_list('post_id', flat=True)

    posts_data = []
    for post in posts:
        likes = Like.objects.filter(post=post).select_related('user')
        posts_data.append({
            'post': post,
            'likes': [like.user for like in likes],
        })

    # Get suggested users (users not followed, exclude self and staff/admin)
    all_users = User.objects.exclude(id=request.user.id).exclude(is_staff=True).exclude(is_superuser=True)
    suggested_users = all_users.exclude(id__in=following_users)[:6]  # Limit to 6 suggestions

    return render(request, 'core/feed.html', {
        'posts_data': posts_data,
        'liked_posts': liked_posts,
        'saved_posts': saved_posts,
        'suggested_users': suggested_users,
    })


@login_required(login_url='login')
def user_profile_view(request, username):
    profile_user = get_object_or_404(User, username=username)

    if profile_user == request.user:
        posts = Post.objects.filter(user=profile_user).order_by('-created_at')
    else:
        posts = Post.objects.filter(user=profile_user, hidden=False).order_by('-created_at')

    is_following = Follow.objects.filter(follower=request.user, following=profile_user).exists()

    posts_data = []
    for post in posts:
        top_comments = post.comments.filter(parent__isnull=True).select_related('user')
        posts_data.append({'post': post, 'top_comments': top_comments})

    liked_posts = Like.objects.filter(user=request.user).values_list('post_id', flat=True)

    # Profile summary metrics
    total_posts = Post.objects.filter(user=profile_user).count()
    followers_count = Follow.objects.filter(following=profile_user).count()
    following_count = Follow.objects.filter(follower=profile_user).count()
    is_owner = profile_user == request.user
    try:
        profile = Profile.objects.get(user=profile_user)
        is_verified = profile.is_verified
    except Profile.DoesNotExist:
        is_verified = False

    return render(request, 'core/user_profile.html', {
        'profile_user': profile_user,
        'posts': posts,
        'is_following': is_following,
        'liked_posts': liked_posts,
        'total_posts': total_posts,
        'followers_count': followers_count,
        'following_count': following_count,
        'is_owner': is_owner,
        'is_verified': is_verified,
    })


@login_required
def inbox_view(request):
    # Get all users who have messaged the current user or vice versa
    sent_messages = Message.objects.filter(sender=request.user).values_list('receiver', flat=True)
    received_messages = Message.objects.filter(receiver=request.user).values_list('sender', flat=True)
    user_ids = set(sent_messages) | set(received_messages)

    conversations = []
    for user_id in user_ids:
        other_user = User.objects.get(id=user_id)
        last_message = Message.objects.filter(
            (Q(sender=request.user) & Q(receiver=other_user)) |
            (Q(sender=other_user) & Q(receiver=request.user))
        ).order_by('-created_at').first()

        unread_count = Message.objects.filter(sender=other_user, receiver=request.user, is_read=False).count()

        conversations.append({
            'user': other_user,
            'last_message': last_message,
            'unread_count': unread_count,
        })

    conversations.sort(key=lambda x: x['last_message'].created_at if x['last_message'] else timezone.now(), reverse=True)

    return render(request, 'core/inbox.html', {'conversations': conversations})


@login_required
def chat_view(request, username):
    other_user = get_object_or_404(User, username=username)

    # Mark messages as read
    Message.objects.filter(sender=other_user, receiver=request.user, is_read=False).update(is_read=True)

    # Get all messages between the two users
    messages = Message.objects.filter(
        (Q(sender=request.user) & Q(receiver=other_user)) |
        (Q(sender=other_user) & Q(receiver=request.user))
    ).order_by('created_at')

    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Message.objects.create(sender=request.user, receiver=other_user, content=content)
        return redirect('chat', username=username)

    return render(request, 'core/chat.html', {
        'other_user': other_user,
        'messages': messages,
    })


@login_required
def send_message_view(request, username):
    other_user = get_object_or_404(User, username=username)

    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Message.objects.create(sender=request.user, receiver=other_user, content=content)

    return redirect('chat', username=username)


@login_required
def search_view(request):
    query = request.GET.get('q', '')
    results = []

    if query:
        # Search users by username, exclude staff/admin and self
        results = User.objects.filter(
            username__icontains=query
        ).exclude(is_staff=True).exclude(is_superuser=True).exclude(id=request.user.id)[:20]

    return render(request, 'core/search.html', {
        'query': query,
        'results': results,
    })


@login_required
def share_post_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    # Get users that the current user is following
    following_users = Follow.objects.filter(follower=request.user).values_list('following', flat=True)
    recipients = User.objects.filter(id__in=following_users)

    if request.method == 'POST':
        recipient_id = request.POST.get('recipient')
        if recipient_id:
            recipient = get_object_or_404(User, id=recipient_id)
            # Send the post as a message
            message_content = f"Shared a post: {post.caption[:50]}... Check it out!"
            Message.objects.create(sender=request.user, receiver=recipient, content=message_content)
            return redirect('chat', username=recipient.username)

    return render(request, 'core/share_post.html', {
        'post': post,
        'recipients': recipients,
    })


@login_required
def save_post_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    saved_post, created = SavedPost.objects.get_or_create(user=request.user, post=post)

    if not created:
        # Already saved, so unsave it
        saved_post.delete()

    return HttpResponseRedirect(reverse('feed'))


@login_required
def saved_posts_view(request):
    saved_posts = SavedPost.objects.filter(user=request.user).select_related('post')
    posts = [saved.post for saved in saved_posts]

    posts_data = []
    for post in posts:
        top_comments = post.comments.filter(parent__isnull=True).select_related('user')
        posts_data.append({'post': post, 'top_comments': top_comments})

    liked_posts = Like.objects.filter(user=request.user).values_list('post_id', flat=True)

    return render(request, 'core/saved_posts.html', {
        'posts': posts,
        'posts_data': posts_data,
        'liked_posts': liked_posts,
    })

