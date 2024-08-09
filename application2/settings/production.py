from .base import *

ALLOWED_HOSTS = ['*']

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2',
#         'NAME': 'application2',
#         'USER': 'postgres',
#         'PASSWORD': 'nats',
#         'HOST': 'localhost',
#         'PORT': '5433'
#     }
# }

# import dj_database_url
# DATABASES['default'] = dj_database_url.parse(os.environ.get('DATABASE_LINK'))
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}