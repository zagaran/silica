# Silica

## Django

Add the following to your settings:
`
INSTALLED_APPS = (
    ...
    'silica.django_app',
    ...
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            ...
            'builtins': [
                'silica.django_app.templatetags.silica',
                'django.contrib.staticfiles.templatetags.staticfiles',
            ],
        },
        ...
    },
]
`

Use the base template silica/base.html

Use the model `silica.django_app.models.TimestampedModel`
