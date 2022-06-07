from django.urls import path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


schema_view = get_schema_view(
    openapi.Info(
        title="API documentation | Hearthstone Deck Helper",
        default_version='v1',
        description='',
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,)      # документация доступна всем
)

urlpatterns = [
    path('api/docs/swagger<format>', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('api/docs/swagger/', schema_view.with_ui(renderer='swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/docs/redoc/', schema_view.with_ui(renderer='redoc', cache_timeout=0), name='schema-redoc'),
]
