from rest_framework.viewsets import ModelViewSet
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer
from accounts.permissions import IsAdmin
from accounts.models import User
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages
from .models import Subscriber
from .forms import CategoryForm, ProductForm
from django.contrib.auth.decorators import login_required
# create your views here
class CategoryViewSet(ModelViewSet):
    """Admin manages categories"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdmin]

class ProductViewSet(ModelViewSet):
    """Admin manages products"""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdmin]
    
#this is the template views for backend 
def category_list_template(request):
    """
    Admin-only: Display all categories in a table.
    """
    if not request.user.is_authenticated or request.user.role != "admin":
        return render(request, "forbidden.html", status=403)

    categories = Category.objects.all()
    return render(request, "category_list.html", {"categories": categories})
#modifying---1
def product_list_template(request, category_slug):
    category = None
    """
    Admin-only: Display all products in a table.
    """
    if not request.user.is_authenticated or request.user.role != "admin":
        return render(request, "forbidden.html", status=403)

    products = Product.objects.filter(available=True)
    categories = Category.objects.all()
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    return render(request, "product_list.html", {
        "products": products, 
        "category": category, 
        "categories": categories})


@login_required
def home(request):
    """
    Root landing page for PrintFlow.
    Acts as a dashboard entry point.
    """
    products = Product.objects.filter(is_active=True)
    return render(request, 'base.html', {'products': products})

@login_required
def subscribe(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if Subscriber.objects.filter(email=email).exists():
            messages.error(request, 'You are already subscribed.')
        else:
            Subscriber.objects.create(email=email)
            messages.success(request, 'Thank you for subscribing!')

        return redirect('subscribe')  
    return render(request, 'footer.html')  


