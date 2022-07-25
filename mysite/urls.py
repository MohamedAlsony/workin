from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.urls import include,path
from django.conf.urls import url
from django.contrib import admin
from django.urls import path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.authentication import SessionAuthentication, TokenAuthentication

schema_view = get_schema_view(
   openapi.Info(
      title="Workin API",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   authentication_classes = [SessionAuthentication,TokenAuthentication],
   permission_classes=[permissions.AllowAny],
)



urlpatterns = [
    url(r'^admin/', admin.site.urls),
    path('api/account/', include('account.urls')),
    path('api/company/', include('companies.urls')),
    path('api/jobs/', include('jobs.urls')),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

