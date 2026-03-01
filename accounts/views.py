from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import render, redirect  
from .models import User
from .serializers import RegisterSerializer, UserProfileSerializer
from .permissions import IsAdmin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as django_logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.shortcuts import get_object_or_404
from .forms import CustomUserCreationForm
#create your views here

class RegisterView(generics.CreateAPIView):
    """
    Public registration endpoint.
    All new users are automatically assigned the CLIENT role.
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(username=username, password=password)

        if user is not None:
            refresh = RefreshToken.for_user(user)

            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "role": user.role,   
                }
            })

        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
    
class LogoutView(APIView):
    """
    Logout user by blacklisting the refresh token (for JWT).
    """
    def post(self, request):
        refresh_token = request.data.get("refresh")
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"message": "Logged out successfully"})
class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    View or update authenticated user's profile.
    """
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user

class UserListView(generics.ListAPIView):
    """
    Admin-only endpoint to list all users.
    """
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAdmin]

class AssignRoleView(APIView):
    """
    Admin-only endpoint to assign a role to a user.
    """
    permission_classes = [IsAdmin]
    
    def put(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        role = request.data.get("role")
        if role not in ["client", "admin", "designer"]:
            return Response({"error": "Invalid role"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.get(id=user_id)
        user.role = role
        user.save()

        return Response({"message": "Role updated successfully"})

def user_list_template(request):
    """
    Admin-only: Render all users in an HTML table.
    """
    if not request.user.is_authenticated or request.user.role != "admin":
        return render(request, "forbidden.html", status=403)

    users = User.objects.all()
    return render(request, "user_list.html", {"users": users})

def user_profile_template(request):
    """
    Render the logged-in user's profile.
    """
    if not request.user.is_authenticated:
        return render(request, "forbidden.html", status=403)

    return render(request, "user_profile.html", {"user": request.user})

@login_required
def post_login_redirect(request):
    """
    Redirect users after login based on role.
    """
    user = request.user

    if user.role == "admin":
        return redirect("/api/view/admin/summary/")
    elif user.role == "designer":
        return redirect("/api/view/designs/")
    elif user.role == "client":
        return redirect("/")
    else:
        return redirect("logout")


def logout(request):
    """
    Log the user out and redirect to login page.
    """
    django_logout(request)
    return redirect("/auth/login/")

def register(request):
    """
    User registration (signup). -using custom User model
    """
    if request.user.is_authenticated:
        return redirect("/auth/redirect/")
    

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("/auth/redirect/")
    else:
        form = CustomUserCreationForm()
    
    return render(request, "register.html", {"form": form})



