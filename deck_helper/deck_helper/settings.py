from pathlib import Path
import os

from django.core.management.utils import get_random_secret_key
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', default=get_random_secret_key())

DEBUG = int(os.environ.get('DEBUG', default=0))

try:
    ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS').split(' ')
except AttributeError:
    ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'modeltranslation',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'cards',
    'decks',
    'accounts',
    'api',
    'debug_toolbar',
    'fontawesomefree',
    'rest_framework',
    'django_filters',
    'drf_yasg',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'deck_helper.middleware.LoggingMiddleware',
]

INTERNAL_IPS = [
    # '127.0.0.1',      # закомментировать = отключить Debug Toolbar локально
]

ROOT_URLCONF = 'deck_helper.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'deck_helper.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': os.environ.get('SQL_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.environ.get('SQL_DATABASE', BASE_DIR / 'db.sqlite3'),
        'USER': os.environ.get('SQL_USER', 'user'),
        'PASSWORD': os.environ.get('SQL_PASSWORD', 'password'),
        'HOST': os.environ.get('SQL_HOST', 'localhost'),
        'PORT': os.environ.get('SQL_PORT', '5432'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# i18n
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

LANGUAGES = (
    ('en', _('English')),
    ('ru', _('Russian')),
)

LOCALE_PATHS = (
    BASE_DIR / 'locale',
)

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CSRF_TRUSTED_ORIGINS = ['http://127.0.0.1', 'http://localhost']
if REMOTE_IP := os.environ.get('REMOTE_IP'):
    CSRF_TRUSTED_ORIGINS.append(f'http://{REMOTE_IP}')

# Максимум записей для выбора в админке
DATA_UPLOAD_MAX_NUMBER_FIELDS = 20000

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
}

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = 'accounts/signin/'

# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.yandex.ru'   # SMTP-сервер исходящей почты
EMAIL_PORT = 465                # 465 (SSL) или 587 (TLS)
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
TEST_EMAIL = os.environ.get('TEST_EMAIL', default=EMAIL_HOST_USER)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,  # не отключать встроенные в Django механизмы логирования
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'formatters': {
        'file': {
            '()': 'django.utils.log.ServerFormatter',
            'format': '\n\n\n[{server_time}]\nlogger:{name} | level:{levelname}\nMsg:\n{message}\n',
            'style': '{',
        },
        'info': {
            '()': 'django.utils.log.ServerFormatter',
            'format': '[{server_time}] | logger:{name} | level:{levelname} | Msg: {message}',
            'style': '{',
        },
        'err': {
            '()': 'django.utils.log.ServerFormatter',
            'format': '\n\n[{server_time}]\nlogger:{name} | level:{levelname}\nMsg:\n{message}\n\n',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
        },
        'info': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'info',
        },
        'err': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
            'formatter': 'err',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'file',
            'filename': BASE_DIR / "logs/info.log"
        },
        'file_err': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'formatter': 'file',
            'filename': BASE_DIR / "logs/errors.log"
        },
    },
    'loggers': {
        'django': {
            'handlers': ['info', 'err'],
            'level': 'WARNING',
            'propagate': True,
        },
        'deck_helper.custom': {
            'handlers': ['err'],
            'level': 'ERROR',
            'propagate': False,
        },
    }
}

DECK_RENDER_MAX_NUMBER = 10     # максимальное число хранимых одновременно рендеров колод

# Список ID карт, расширяющих колоду дополнительными картами.
# При пустом списке никакие доп. карты не будут отображаться в колоде.
KNOWN_EXPANDER_ID_LIST = [90749]

# API Hearthstone (RapidAPI)
RAPIDAPI_BASEURL = 'https://omgvamp-hearthstone-v1.p.rapidapi.com/'
RAPIDAPI_HOST = 'omgvamp-hearthstone-v1.p.rapidapi.com'
X_RAPIDARI_KEY = os.environ.get('X_RAPIDARI_KEY')

MODEL_TRANSLATION_FILE = BASE_DIR / 'locale' / 'translations.json'

# Celery & Redis
REDIS_HOST_NAME = 'broker'           # имя сервиса с Redis в docker-compose
REDIS_PORT = os.environ.get('REDIS_PORT', default='6379')
REDIS_HOST_PASSWORD = os.environ.get('REDIS_HOST_PASSWORD', '')
REDIS_HOST = f':{REDIS_HOST_PASSWORD}@{REDIS_HOST_NAME}' if REDIS_HOST_PASSWORD else REDIS_HOST_NAME

CELERY_BROKER_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'
CELERY_BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 3600}
CELERY_RESULT_BACKEND = f'redis://{REDIS_HOST}:{REDIS_PORT}/1'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': f'redis://{REDIS_HOST}:{REDIS_PORT}/2',
    }
}

# Время жизни кэша (в секундах)
CACHE_TTL = 60
