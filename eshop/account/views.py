from datetime import datetime, timedelta

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404
from django.utils.crypto import get_random_string
from django.core.mail import send_mail

from .models import Profile
from .serializers import SignupSerializer, UserSerializer


# Create your views here.


@api_view(["POST"])
def register(request):
    data = request.data
    serializer = SignupSerializer(data=data, many=False)
    if serializer.is_valid():
        if not User.objects.filter(username=data["email"]).exists():
            user = User.objects.create(
                first_name=data["first_name"],
                last_name=data["last_name"],
                email=data["email"],
                username=data["email"],
                password=make_password(data["password"])
            )

            return Response({"message": "User registered."}, status=status.HTTP_201_CREATED)

        else:
            return Response({"message": "User already exists"}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(serializer.errors)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    user = UserSerializer(request.user, many=False)
    return Response(user.data)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_user_profile(request):

    user = request.user
    data = request.data

    user.first_name = data["first_name"]
    user.last_name = data["last_name"]
    user.email = data["email"]
    user.username = data["username"]

    if data["password"] != "":
        user.password = make_password(data["password"])

    user.save()

    serializer = UserSerializer(user, many=False)

    return Response(serializer.data)


def get_current_host(request):
    protocol = request.is_secure() and "https" or "http"
    host = request.get_host()

    return f"{protocol}://{host}/"


@api_view(["POST"])
def forgot_password(request):
    data = request.data
    user = get_object_or_404(User, email=data["email"])

    token = get_random_string(40)
    expire_date = datetime.now() + timedelta(minutes=30)

    user.profile.reset_password_token = token
    user.profile.reset_password_expire = expire_date
    user.profile.save()

    host = get_current_host(request)

    link = f"{host}api/reset_password/{token}"
    body = f"Your password reset link is {link}"

    send_mail(
        "Password Reset for eShop",
        body,
        "noreply@eshop.com",
        [data["email"]]
    )

    return Response({"message": "Password reset email sent to: {email}".format(email=data["email"])})


@api_view(["POST"])
def reset_password(request, token):
    data = request.data
    user = get_object_or_404(User, profile__reset_password_token=token)

    if user.profile.reset_password_expire.replace(tzinfo=None) < datetime.now():
        return Response({"error": "Token has expired."}, status=status.HTTP_400_BAD_REQUEST)

    if data["password"] != data["confirmPassword"]:
        return Response({"error": "Password and confirm password do not match"})

    user.password = make_password(data["password"])
    user.profile.reset_password_token = ""
    user.profile.reset_password_expire = None
    user.profile.save()
    user.save()

    return Response({"message": "Password reset successfully."})
