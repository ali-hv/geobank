from celery import shared_task
from .utils import populate_geobank_data

@shared_task
def populate_geobank_task():
    populate_geobank_data()
