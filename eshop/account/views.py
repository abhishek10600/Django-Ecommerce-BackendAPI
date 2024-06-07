
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password


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
