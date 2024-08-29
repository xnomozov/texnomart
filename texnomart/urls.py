from django.urls import path
from root import custom_obtain_view
from texnomart.views.texnomart import views

urlpatterns = [
    # INDEX
    path('', views.AllProductView.as_view(), name='index'),

    # CATEGORIES
    path('categories/', views.CategoryView.as_view(), name='categories'),
    path('category/<slug:slug>/', views.CategoryProductsView.as_view(), name='category'),
    path('category/add/category/', views.AddCategoryView.as_view(), name='category-add'),
    path('category/<slug:slug>/delete/', views.DeleteCategoryView.as_view(), name='category'),
    path('category/<slug:slug>/edit/', views.EditCategoryView.as_view(), name='category-edit'),

    # PRODUCTS
    path('product/detail/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('product/<int:pk>/delete/', views.DeleteProductView.as_view(), name='product-delete'),
    path('product/<int:pk>/edit/', views.EditProductView.as_view(), name='product-edit'),

    # ATTRIBUTES
    path('attribute-key/', views.AttributeKeyView.as_view(), name='attribute-key'),
    path('attribute-value/', views.AttributeValueView.as_view(), name='attribute-value'),

    # auth
    path("login/", custom_obtain_view.LoginView.as_view(), name="user_login"),
    path("register/", custom_obtain_view.RegisterView.as_view(), name="user_register"),
    path("logout/", custom_obtain_view.LogoutView.as_view(), name="user_logout")

]
