from django.urls import path
from . import views
app_name = 'products'

urlpatterns = [

    # CATEGORIES
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('categories/create/', views.CreateCategoryView.as_view(), name='category_create'),
    path('categories/<int:pk>/update/', views.UpdateCategoryView.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', views.DeleteCategoryView.as_view(), name='category_delete'),
    # PRODUCTS
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/featured/', views.FeaturedProductsView.as_view(), name='featured_products'),
    path('products/create/', views.CreateProductView.as_view(), name='product_create'),
    path('products/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('products/<int:pk>/update/', views.UpdateProductView.as_view(), name='product_update'),
    path('products/<int:pk>/delete/', views.DeleteProductView.as_view(), name='product_delete'),
    # PUBLIC (No Auth)
    path('public/products/<int:pk>/', views.PublicProductDetailView.as_view(), name='public_product_detail'),
    path('public/products/', views.PublicProductListView.as_view(), name='public_products'),
    path('public/categories/', views.PublicCategoryListView.as_view(), name='public_categories'),
    path('public/categories/<int:pk>/', views.PublicCategoryDetailView.as_view(), name='public_category_detail'),
]