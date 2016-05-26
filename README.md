# Silica

Silica is a collection of tools to reduce common code used in the frontend-backend interfacing of web sites.
The initial version is intended primarily for combining Django and Angular, but the project is designed to eventually support other frameworks.
**This is an early phase project and the interface and behavior of components may change radically before the final release.**

If you are interested in helping, we are seeking collaborators.  Please contact zags [at] zagaran.com if you are interested.

## Django

Add the following to your settings:

```
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
```

Use the base template silica/base.html

Use the model `silica.django_app.models.TimestampedModel`
