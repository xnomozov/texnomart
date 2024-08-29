"""
URL configuration for root project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from root.custom_obtain_view import CustomAuthToken

from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from debug_toolbar.toolbar import debug_toolbar_urls


from root import settings
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


urlpatterns = [
                  path('admin/', admin.site.urls),
                  path('texnomart-uz/', include('texnomart.urls')),
                  path('api-auth/', include('rest_framework.urls')),
                  path('api/token-auth/', CustomAuthToken.as_view(), name='api_token_auth'),
                  path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
                  path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += debug_toolbar_urls()


