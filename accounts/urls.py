from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'accounts'

urlpatterns = [
    # =====================
    # AUTHENTICATION
    # =====================
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/profile/', views.ProfileView.as_view(), name='profile'),
    path('auth/change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('auth/password-reset/', views.PasswordResetRequestView.as_view(), name='password_reset'),
    path('auth/password-reset/confirm/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    # =====================
    # REGISTRATION
    # =====================
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/register-company/', views.CompanyRegistrationView.as_view(), name='register_company'),
    
    # =====================
    # USER MANAGEMENT
    # =====================
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/<int:pk>/deactivate/', views.DeactivateUserView.as_view(), name='user_deactivate'),
    path('users/<int:pk>/change-role/', views.ChangeUserRoleView.as_view(), name='change_role'),
    
    # =============
    # INVITATIONS
    # ============
    path('invitations/', views.InvitationListView.as_view(), name='invitation_list'),
    path('invitations/<str:token>/', views.InvitationDetailView.as_view(), name='invitation_detail'),
    path('invitations/<int:pk>/cancel/', views.CancelInvitationView.as_view(), name='invitation_cancel'),
    path('invitations/<int:pk>/resend/', views.ResendInvitationView.as_view(), name='invitation_resend'),
]