from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import RedirectView

from core.views import contact, statistics, api_greeting
from .yasg import urlpatterns as doc_urlpatterns

urlpatterns = [
    path('', RedirectView.as_view(url='decks/', permanent=True), name='home'),
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('api-auth/', include('rest_framework.urls')),      # для тестирования API через веб-интерфейс
    path('api/v1/', include('api.urls')),
]

# переводимые приложения
urlpatterns += i18n_patterns(
    path('cards/', include('cards.urls')),
    path('decks/', include('decks.urls')),
    path('accounts/', include('accounts.urls')),
    path('contact/', contact, name='contact'),
    path('statistics/', statistics, name='statistics'),
    path('api/', api_greeting, name='api_greeting'),
)

urlpatterns += doc_urlpatterns

if settings.DEBUG:
    # Подключение статических и медиа- файлов
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Django Debug Toolbar
    import debug_toolbar

    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
