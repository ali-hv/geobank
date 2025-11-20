from django.core.management.base import BaseCommand
from geobank.utils import populate_geobank_data


class Command(BaseCommand):
    help = 'Populate GeoBank data with translations based on settings.LANGUAGES'

    def add_arguments(self, parser):
        parser.add_argument(
            '--background',
            action='store_true',
            help='Run the population task in the background using Celery',
        )

    def handle(self, *args, **options):
        if options['background']:
            try:
                from geobank.tasks import populate_geobank_task
                populate_geobank_task.delay()
                self.stdout.write(self.style.SUCCESS('GeoBank population task started in background.'))
            except ImportError:
                self.stdout.write(self.style.ERROR('Celery is not installed or configured. Running synchronously.'))
                populate_geobank_data()
                self.stdout.write(self.style.SUCCESS('GeoBank population completed successfully.'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error starting background task: {e}'))
        else:
            self.stdout.write('Starting GeoBank population...')
            populate_geobank_data()
            self.stdout.write(self.style.SUCCESS('GeoBank population completed successfully.'))

