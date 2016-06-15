
# minimal Django config for running tests

INSTALLED_APPS = (
    'silica.django_app',
    'tests',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'builtins': [
                'silica.django_app.templatetags.silica',
                'django.contrib.staticfiles.templatetags.staticfiles',
            ],
        },
    },
]

SECRET_KEY = 'abcde12345'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'testdatabase',
    }
}
