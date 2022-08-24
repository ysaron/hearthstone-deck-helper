from django.views.decorators.cache import cache_page
from django.conf import settings


class CacheMixin:
    """ Подключает кэширование для CBV """
    @classmethod
    def as_view(cls, **initkwargs):
        return cache_page(settings.CACHE_TTL)(super().as_view(**initkwargs))
