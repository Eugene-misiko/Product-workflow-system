from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'accounts'

urlpatterns = [
    # AUTH
    path('auth/login/', views.LoginView.as_view()),
    path('auth/logout/', views.LogoutView.as_view()),
    path('auth/refresh/', TokenRefreshView.as_view()),
    path('auth/profile/', views.ProfileView.as_view()),
    path('auth/me/', views.ProfileView.as_view()),  # optional
    path('auth/change-password/', views.ChangePasswordView.as_view()),
    path('auth/password-reset/', views.PasswordResetRequestView.as_view()),
    path('auth/password-reset/confirm/', views.PasswordResetConfirmView.as_view()),

    # REGISTRATION
    path('auth/register/', views.RegisterWithInvitationView.as_view()),
    path('auth/register-user/', views.RegisterView.as_view()),
    path('auth/register-company/', views.CompanyRegistrationView.as_view()),

    # USERS
    path('users/', views.UserListView.as_view()),
    path('users/<int:pk>/', views.UserDetailView.as_view()),
    path('users/<int:pk>/deactivate/', views.DeactivateUserView.as_view()),
    path('users/<int:pk>/change-role/', views.ChangeUserRoleView.as_view()),

    # INVITATIONS (FIXED)
    path('invitations/', views.InvitationListView.as_view()),
    path('invitations/<str:token>/', views.InvitationDetailView.as_view()),
    path('invitations/<str:token>/cancel/', views.CancelInvitationView.as_view()),
    path('invitations/<str:token>/resend/', views.ResendInvitationView.as_view()),
]