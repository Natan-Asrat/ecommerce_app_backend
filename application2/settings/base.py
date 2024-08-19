from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

import os
import dotenv
dotenv.read_dotenv()
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
# DEBUG = os.environ.get('DEBUG').lower() == 'true' if os.environ.get('DEBUG') else False
DEBUG = True
ALLOW_FREE_POST = os.environ.get("ALLOW_FREE_POST").lower() == 'true' if os.environ.get('ALLOW_FREE_POST') else True
COMPRESS_IMAGES = os.environ.get("COMPRESS_IMAGES").lower() == 'true' if os.environ.get('COMPRESS_IMAGES') else True
ADS_INITIAL_POSITION = int(os.environ.get('ADS_INITIAL_POSITION', 2)) 
INTERVAL_BETWEEN_ADS = int(os.environ.get('INTERVAL_BETWEEN_ADS', 3))

NEW_POST_RECOMMENDATION_LIMIT = int(os.environ.get('NEW_POST_RECOMMENDATION_LIMIT', 30))
FOLLOWING_BASED_RECOMMENDATION_LIMIT = int(os.environ.get('FOLLOWING_BASED_RECOMMENDATION_LIMIT', 35))
CATEGORY_BASED_RECOMMENDATION_LIMIT = int(os.environ.get('CATEGORY_BASED_RECOMMENDATION_LIMIT', 5))
IICF_RECOMMENDATION_LIMIT = int(os.environ.get('IICF_RECOMMENDATION_LIMIT', 45))
UUCF_RECOMMENDATION_LIMIT = int(os.environ.get('UUCF_RECOMMENDATION_LIMIT', 20))
UCCF_RECOMMENDATION_LIMIT = int(os.environ.get('UCCF_RECOMMENDATION_LIMIT', 15))
RECOMMENDATION_LIMIT = int(os.environ.get('RECOMMENDATION_LIMIT', 25))
POSTS_INITIAL_IICF = int(os.environ.get('POSTS_INITIAL_IICF', 5))
USERS_INITIAL_IICF = int(os.environ.get('USERS_INITIAL_IICF', 20))

COIN_TO_MONEY_MULTIPLIER = int(os.environ.get('COIN_TO_MONEY_MULTIPLIER', 20))
PRICE_PER_CATEGORY = int(os.environ.get('PRICE_PER_CATEGORY', 2))
MINIMUM_TO_STANDARD_MULTIPLIER = int(os.environ.get('MINIMUM_TO_STANDARD_MULTIPLIER', 3))
INCREMENT_MULTIPLE = int(os.environ.get('INCREMENT_MULTIPLE', 1))
PREMIUM_MULTIPLIER = int(os.environ.get('PREMIUM_MULTIPLIER', 1.5))
COUNT_ADS_THRESHOLD_BEFORE_AVERAGING_FOR_STANDARD = int(os.environ.get('COUNT_ADS_THRESHOLD_BEFORE_AVERAGING_FOR_STANDARD', 5))

USERS_INITIAL_UUCF = int(os.environ.get('USERS_INITIAL_UUCF', 20))

CATEGORIES_INITIAL_UCCF = int(os.environ.get('CATEGORIES_INITIAL_UCCF', 5))
SELLERS_INITIAL_UCCF = int(os.environ.get('SELLERS_INITIAL_UCCF', 20))

FOLLOWING_INITIAL_FOLLOWING = int(os.environ.get('FOLLOWING_INITIAL_FOLLOWING', 50))

CATEGORY_REDUCER_CONSTANT = int(os.environ.get('CATEGORY_REDUCER_CONSTANT', 100))
USER_REDUCER_CONSTANT = int(os.environ.get('USER_REDUCER_CONSTANT', 10))

FIREBASE_ACCOUNT_TYPE = os.environ.get('FIREBASE_ACCOUNT_TYPE')
FIREBASE_PROJECT_ID = os.environ.get('FIREBASE_PROJECT_ID')
FIREBASE_PRIVATE_KEY_ID = os.environ.get('FIREBASE_PRIVATE_KEY_ID')
FIREBASE_PRIVATE_KEY = os.environ.get('FIREBASE_PRIVATE_KEY')
FIREBASE_CLIENT_EMAIL = os.environ.get('FIREBASE_CLIENT_EMAIL')
FIREBASE_CLIENT_ID = os.environ.get('FIREBASE_CLIENT_ID')
FIREBASE_AUTH_URI = os.environ.get('FIREBASE_AUTH_URI')
FIREBASE_TOKEN_URI = os.environ.get('FIREBASE_TOKEN_URI')
FIREBASE_AUTH_PROVIDER_X509_CERT_URL = os.environ.get('FIREBASE_AUTH_PROVIDER_X509_CERT_URL')
FIREBASE_CLIENT_X509_CERT_URL = os.environ.get('FIREBASE_CLIENT_X509_CERT_URL')
SMS_GATEWAY_URL = os.environ.get('SMS_GATEWAY_URL')

CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')
# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'drf_spectacular',
    'posts.apps.PostsConfig',
    'debug_toolbar',
    'corsheaders',
    'fcm_django',
    # 'whitenoise.runserver_nostatic'
]
INTERNAL_IPS = [
    '127.0.0.1',
]
# MIDDLEWARE = [
#     'debug_toolbar.middleware.DebugToolbarMiddleware',
#     'django.middleware.security.SecurityMiddleware',
#     "whitenoise.middleware.WhiteNoiseMiddleware",
#     'django.contrib.sessions.middleware.SessionMiddleware',
#     'django.middleware.common.CommonMiddleware',
#     'django.middleware.csrf.CsrfViewMiddleware',
#     'django.contrib.auth.middleware.AuthenticationMiddleware',
#     'django.contrib.messages.middleware.MessageMiddleware',
#     'django.middleware.clickjacking.XFrameOptionsMiddleware',
# ]
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    # Debug Toolbar Middleware (for development)
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    
    # Security Middleware
    'django.middleware.security.SecurityMiddleware',
    
    # Static File Middleware
    "whitenoise.middleware.WhiteNoiseMiddleware",
    
    # Session Middleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    
    # Common Middleware
    'django.middleware.common.CommonMiddleware',
    
    # CSRF Middleware
    'django.middleware.csrf.CsrfViewMiddleware',
    
    # Authentication Middleware
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    
    # Message Middleware
    'django.contrib.messages.middleware.MessageMiddleware',
    
    # Clickjacking Middleware
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOW_ALL_ORIGINS = True
CORS_ORIGIN_ALLOW_ALL = True

ROOT_URLCONF = 'application2.urls'

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

WSGI_APPLICATION = 'application2.wsgi.application'


CONN_MAX_AGE = None
AUTH_USER_MODEL = 'posts.User'
# from neomodel import config
# config.DATABASE_URL = 'bolt://neo4j:12345678@localhost:7687/application2'
# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = '/static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
# DEBUG_TOOLBAR_PANELS = [
#     'debug_toolbar.panels.profiling.ProfilingPanel'
# ]


 
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


SPECTACULAR_SETTINGS = {
    "TITLE": "Emi Shop Ecommerce App Backend",
}
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'posts.authentication.FirebaseAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES':[
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

import cloudinary
          
cloudinary.config( 
  cloud_name = CLOUDINARY_CLOUD_NAME, 
  api_key = CLOUDINARY_API_KEY, 
  api_secret = CLOUDINARY_API_SECRET,
  secure = True
)