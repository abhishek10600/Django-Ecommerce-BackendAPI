from django.urls import path
from .views import register, get_current_user, update_user_profile, forgot_password, reset_password

urlpatterns = [
    path("register/", register, name="register"),
    path("me/", get_current_user, name="get_current_user"),
    path("me/update/", update_user_profile, name="update_user_profile"),
    path("forgot_password/", forgot_password, name="forgot_password"),
    path("reset_password/<str:token>/", reset_password, name="reset_password")
]
