from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (RegisterView,LogoutView,LoginView,UserProfileView,UserListView,AssignRoleView,
                    ChangePasswordView,PasswordResetRequestView, PasswordResetConfirmView)
urlpatterns = [
    # Registration
    path("register/", RegisterView.as_view(), name="register"),
    # JWT login/logout
    path("login/", LoginView.as_view(), name="login_view"),
    path("logout/", LogoutView.as_view(), name="logout"),
    # Profile
    path("profile/", UserProfileView.as_view(), name="profile"),
    # Admin
    path("users/", UserListView.as_view(), name="users"),
    path("users/<int:user_id>/role/", AssignRoleView.as_view(), name="users_id"),
    #
    path("reset_confirm/", PasswordResetConfirmView.as_view(), name="reset_confirm"),
    path("request_reset/", PasswordResetRequestView.as_view(), name="rerequest_reset"),
    path("change_password/", ChangePasswordView.as_view(), name="change_password"),
]