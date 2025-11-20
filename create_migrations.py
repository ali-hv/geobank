import os
import sys
import django
from django.conf import settings

# Add src to path
sys.path.insert(0, os.path.abspath('src'))

# Configure Django settings
settings.configure(
    DEBUG=True,
    SECRET_KEY='secret',
    INSTALLED_APPS=[
        'geobank',
    ],
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    },
    DEFAULT_AUTO_FIELD='django.db.models.BigAutoField',
)

django.setup()

from django.core.management import call_command

if __name__ == '__main__':
    call_command('makemigrations', 'geobank')
