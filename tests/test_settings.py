
import os

SECRET_KEY = 'fake-key'

DIRNAME = os.path.dirname(__file__)
INSTALLED_APPS = [
    'django.contrib.staticfiles',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.admin',
    'django.contrib.messages',
]
INSTALLED_APPS += [
    'djangowkb',
    'tests',
    'leaflet'
]

DATABASES = {'default': {
                        'ENGINE': 'django.db.backends.sqlite3',
                        'NAME': os.path.join(DIRNAME, 'database.db'),
                        }
             }

STATIC_URL = '/static/'

MIDDLEWARE = [
                'django.contrib.auth.middleware.AuthenticationMiddleware',
                'django.contrib.messages.middleware.MessageMiddleware',
                'django.contrib.sessions.middleware.SessionMiddleware',
            ]

TEMPLATES = [{
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'OPTIONS': {
                    'context_processors': [
                        'django.template.context_processors.debug',
                        'django.template.context_processors.request',
                        'django.contrib.auth.context_processors.auth',
                        'django.contrib.messages.context_processors.messages',
                    ]
                },
                'APP_DIRS': True,
            }]

