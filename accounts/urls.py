from django.urls import path
from django.contrib.auth import views as auth_views
from .views import RegisterView, LogoutView, UserProfileView, UserListView, AssignRoleView

urlpatterns = [
    # Registration
    path("register/", RegisterView.as_view(), name='register'),

    # JWT login/logout (for API)
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page='login'), name="logout"),

    # Password management
    path("password_change/", auth_views.PasswordChangeView.as_view(template_name="accounts/password_change.html"), name="password_change"),
    path("password_change/done/", auth_views.PasswordChangeDoneView.as_view(template_name="accounts/password_change_done.html"), name="password_change_done"),
    path("password_reset/", auth_views.PasswordResetView.as_view(template_name="accounts/password_reset.html"), name="password_reset"),
    path("password_reset/done/", auth_views.PasswordResetDoneView.as_view(template_name="accounts/password_reset_done.html"), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(template_name="accounts/password_reset_confirm.html"), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(template_name="accounts/password_reset_complete.html"), name="password_reset_complete"),

    # Profile
    path("profile/", UserProfileView.as_view(), name='profile'),

    # Admin
    path("users/", UserListView.as_view(), name='users'),
    path("users/<int:user_id>/role/", AssignRoleView.as_view(), name='users_id'),
]

