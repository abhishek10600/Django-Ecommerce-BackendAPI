from django.urls import path
from .views import register, get_current_user, update_user_profile

urlpatterns = [
    path("register/", register, name="register"),
    path("me/", get_current_user, name="get_current_user"),
    path("me/update/", update_user_profile, name="update_user_profile")
]
