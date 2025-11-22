# GeoBank

A Django package that provides models for Countries and Cities with translation support using `django-modeltranslation`.

## Installation

1. Install the package:
   ```bash
   pip install GeoBank
   ```

2. Add `geobank` and `modeltranslation` to your `INSTALLED_APPS` in `settings.py`. **Note:** `modeltranslation` must be added **before** `django.contrib.admin`.

   ```python
   INSTALLED_APPS = [
       'modeltranslation',
       'django.contrib.admin',
       # ...
       'geobank',
   ]
   ```

3. Configure your languages in `settings.py`:
   ```python
   LANGUAGES = (
       ('en', 'English'),
       ('fa', 'Persian'),
       # ... other languages
   )
   ```

4. Run migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. Populate the database:
   ```bash
   python manage.py populate_geobank
   ```
   
   To run in the background (requires Celery):
   ```bash
   python manage.py populate_geobank --background
   ```

   To choose the cities population:
   ```bash
   python manage.py populate_geobank --population-gte {500, 1000, 5000, 15000}
   ```

## Requirements

- Django >= 3.2
- django-modeltranslation >= 0.18.0
- Pillow >= 9.0
- Celery (optional, for background tasks)
- tqdm (for progress bars)
- requests

## TODO
- [ ] Improve data gathering and population faster using async scrips
- [ ] Add more fields to models
