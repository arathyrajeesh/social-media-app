import random
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from .forms import RegisterForm
from .models import Profile
from django.contrib import messages

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
                return render(request, 'core/welcome.html', {'user': user})
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
