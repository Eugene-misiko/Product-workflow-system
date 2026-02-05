from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView
    
from .views import RegisterView,LogoutView,UserProfileView,UserListView,AssignRoleView
urlpatterns = [
    # Auth
    path("register/", RegisterView.as_view()),
    path("login/", TokenObtainPairView.as_view()),
    path("token/refresh/", TokenRefreshView.as_view()),
    path("logout/", LogoutView.as_view()),

    # Profile
    path("profile/", UserProfileView.as_view()),

    # Admin
    path("users/", UserListView.as_view()),
    path("users/<int:user_id>/role/", AssignRoleView.as_view()),
]
