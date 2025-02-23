from os import environ
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = environ.get("DJANGO_SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True if environ.get("DEBUG") == "1" else False

if not DEBUG:
    CSRF_COOKIE_SECURE = True #to avoid transmitting the CSRF cookie over HTTP accidentally.
    SESSION_COOKIE_SECURE = True #to avoid transmitting the session cookie over HTTP accidentally.
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_SSL_REDIRECT = True
    ALLOWED_HOSTS = ["194.146.123.65", "admin-napsv.ir" ,"napsv.ir"]
else:
    ALLOWED_HOSTS = ['127.0.0.1', "*"]
    CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

LOGIN_URL = "/accounts/login/"


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'compressor',
    'django_celery_beat',
    'accounts.apps.AccountsConfig',
    'configs.apps.ConfigsConfig',
    'customers.apps.CustomersConfig',
    'finance.apps.FinanceConfig',
    'logs.apps.LogsConfig',
    'sellers.apps.SellersConfig',
    'servers.apps.ServersConfig',
    'bot.apps.BotConfig',
    'side_bot.apps.SideBotConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'SanaeiBot.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'accounts.context_processors.global_vars',
            ],
        },
    },
]

WSGI_APPLICATION = 'SanaeiBot.wsgi.application'

AUTH_USER_MODEL = "accounts.User"


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        "OPTIONS": {
                "timeout": 20,
            }
    },

}



# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2',
#         'NAME': 'sanaeibot',
#         'USER': 'sezar',
#         'PASSWORD': 'sina0610348736',
#         'HOST': 'localhost',
#         'PORT': '',
#     }
# }


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




LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


STATIC_URL = '/static/'
STATIC_ROOT = environ.get('STATIC_ROOT')
STATICFILES_FINDERS = ("compressor.finders.CompressorFinder",)
COMPRESS_PRECOMPILERS = (
    ('text/x-scss', 'django_libsass.SassCompiler'),
)


MEDIA_URL = '/media/'
MEDIA_ROOT = environ.get('MEDIA_ROOT')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
