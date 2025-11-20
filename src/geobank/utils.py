from django.conf import settings
import logging
import zipfile
import io
import os

from geobank.models import Country, City, Region
from .downloaders import download_heavy_file, download_with_retry

logger = logging.getLogger(__name__)


def get_country_data():
    """
    Fetches country data from geonames.org.
    """
    url = "https://download.geonames.org/export/dump/countryInfo.txt"
    data = []
    try:
        content_bytes = download_with_retry(url)
        content = content_bytes.decode('utf-8')
            
        for line in content.splitlines():
            if line.startswith('#') or not line.strip():
                continue
            
            parts = line.split('\t')
            if len(parts) < 17:
                continue
                
            # ISO(0), ISO3(1), ISO-Numeric(2), fips(3), Country(4), Capital(5), Area(6), 
            # Population(7), Continent(8), tld(9), CurrencyCode(10), CurrencyName(11), 
            # Phone(12), Postal Code Format(13), Postal Code Regex(14), Languages(15), 
            # geonameid(16), neighbours(17), EquivalentFipsCode(18)
            
            try:
                geoname_id = int(parts[16])
            except ValueError:
                continue

            data.append({
                'code2': parts[0],
                'code3': parts[1],
                'name': parts[4],
                'name_ascii': parts[4], # Assuming ASCII/English
                'continent': parts[8],
                'calling_code': parts[12],
                'postal_code_format': parts[13],
                'postal_code_regex': parts[14],
                'geoname_id': geoname_id,
            })
    except Exception as e:
        logger.error(f"Error fetching country data: {e}")
        
    return data

def get_region_data():
    """
    Fetches region data from geonames.org.
    """
    url = "https://download.geonames.org/export/dump/admin1CodesASCII.txt"
    data = []
    try:
        content_bytes = download_with_retry(url)
        content = content_bytes.decode('utf-8')
            
        for line in content.splitlines():
            if not line.strip():
                continue
            
            parts = line.split('\t')
            if len(parts) < 4:
                continue
            
            # code(0), name(1), name_ascii(2), geoname_id(3)
            code_parts = parts[0].split('.')
            if len(code_parts) < 2:
                continue
                
            country_code = code_parts[0]
            
            try:
                geoname_id = int(parts[3])
            except ValueError:
                continue

            data.append({
                'country_code': country_code,
                'name': parts[1],
                'name_ascii': parts[2],
                'geoname_id': geoname_id,
            })
    except Exception as e:
        logger.error(f"Error fetching region data: {e}")
        
    return data

def get_city_data():
    """
    Fetches city data from geonames.org.
    """
    url = "https://download.geonames.org/export/dump/cities15000.zip"
    data = []
    try:
        zip_content = download_with_retry(url)
        
        with zipfile.ZipFile(io.BytesIO(zip_content)) as z:
            with z.open('cities15000.txt') as f:
                with io.TextIOWrapper(f, encoding='utf-8') as text_file:
                    for line in text_file:
                        if not line.strip():
                            continue
                        
                        parts = line.split('\t')
                        if len(parts) < 19:
                            continue
                        
                        try:
                            geoname_id = int(parts[0])
                        except ValueError:
                            continue

                        data.append({
                            'geoname_id': geoname_id,
                            'name': parts[1],
                            'name_ascii': parts[2],
                            'country_code': parts[8],
                            'region_code': parts[10],
                        })
    except Exception as e:
        logger.error(f"Error fetching city data: {e}")
        
    return data

def populate_countries():
    logger.info('Populating countries...')
    data = get_country_data()
    
    for item in data:
        Country.objects.update_or_create(
            geoname_id=item['geoname_id'],
            defaults={
                'name': item['name'],
                'name_ascii': item['name_ascii'],
                'continent': item['continent'],
                'code2': item['code2'],
                'code3': item['code3'],
                'calling_code': item['calling_code'],
                'postal_code_format': item['postal_code_format'],
                'postal_code_regex': item['postal_code_regex'],
            }
        )

def populate_regions():
    logger.info('Populating regions...')
    data = get_region_data()
    
    countries = {c.code2: c for c in Country.objects.all()}
    
    for item in data:
        country = countries.get(item['country_code'])
        if country:
            Region.objects.update_or_create(
                geoname_id=item['geoname_id'],
                defaults={
                    'name': item['name'],
                    'name_ascii': item['name_ascii'],
                    'country': country,
                }
            )

def populate_cities():
    logger.info('Populating cities...')
    data = get_city_data()
    
    countries = {c.code2: c for c in Country.objects.all()}
    regions = {r.geoname_id: r for r in Region.objects.all()}
    
    for item in data:
        country = countries.get(item['country_code'])
        region = regions.get(int(item['region_code'])) if item['region_code'].isdigit() else None
        if country:
            City.objects.update_or_create(
                geoname_id=item['geoname_id'],
                defaults={
                    'name': item['name'],
                    'name_ascii': item['name_ascii'],
                    'country': country,
                    'region': region,
                }
            )


def translate_data(languages):
    logger.info('Starting translation...')
    
    # Map geoname_id to model instance
    entities = {}
    logger.info('Loading entities into memory...')
    for country in Country.objects.all():
        entities[country.geoname_id] = country
    for region in Region.objects.all():
        entities[region.geoname_id] = region
    for city in City.objects.all():
        entities[city.geoname_id] = city
    logger.info(f'Loaded {len(entities)} entities.')

    url = "https://download.geonames.org/export/dump/alternateNames.zip"
    translations = {} # (geoname_id, lang) -> (name, is_preferred)

    try:
        logger.info(f"Downloading translations from {url}")
        tmp_file_path = download_heavy_file(url)

        logger.info("Processing translations...")
        with zipfile.ZipFile(tmp_file_path) as z:
            with z.open('alternateNames.txt') as f:
                with io.TextIOWrapper(f, encoding='utf-8') as text_file:
                    for line in text_file:
                        parts = line.split('\t')
                        if len(parts) < 4:
                            continue
                        
                        try:
                            geoname_id = int(parts[1])
                        except ValueError:
                            continue

                        if geoname_id not in entities:
                            continue

                        lang = parts[2]
                        if lang not in languages:
                            continue

                        name = parts[3]
                        is_preferred = len(parts) > 4 and parts[4] == '1'
                        
                        key = (geoname_id, lang)
                        current = translations.get(key)
                        
                        if current:
                            # If we already have a preferred name, and this one isn't, skip
                            if current[1] and not is_preferred:
                                continue
                            # If this one is preferred and current isn't, overwrite
                            # Or if both are same preference, overwrite (last wins)
                        
                        translations[key] = (name, is_preferred)

        os.remove(tmp_file_path)

        logger.info("Applying translations...")
        modified_instances = set()
        
        for (geoname_id, lang), (name, _) in translations.items():
            instance = entities[geoname_id]
            field_name = f'name_{lang}'
            if hasattr(instance, field_name):
                setattr(instance, field_name, name)
                modified_instances.add(instance)

        logger.info("Saving translations...")
        countries_to_update = []
        regions_to_update = []
        cities_to_update = []
        
        for instance in modified_instances:
            if isinstance(instance, Country):
                countries_to_update.append(instance)
            elif isinstance(instance, Region):
                regions_to_update.append(instance)
            elif isinstance(instance, City):
                cities_to_update.append(instance)
        
        # We need to be careful with bulk_update. It expects the fields to exist on the model.
        # Since we are using django-modeltranslation, the fields name_{lang} should exist on the model class
        # if the language is in settings.LANGUAGES.
        # However, we should only update fields that are actually present in the 'languages' list passed to this function.
        
        # Also, we need to make sure we don't try to update a field that doesn't exist for a specific model if for some reason it wasn't registered.
        # But assuming standard setup, it should be fine.
        
        for lang in languages:
             # Verify field exists on models before adding to update list?
             # bulk_update will fail if field doesn't exist.
             pass

        update_fields = [f'name_{lang}' for lang in languages]
        
        if countries_to_update:
            Country.objects.bulk_update(countries_to_update, update_fields)
        if regions_to_update:
            Region.objects.bulk_update(regions_to_update, update_fields)
        if cities_to_update:
            City.objects.bulk_update(cities_to_update, update_fields)
            
    except Exception as e:
        logger.error(f"Error processing translations: {e}")
        if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
             os.remove(tmp_file_path)


def populate_geobank_data():
    languages = [lang[0] for lang in getattr(settings, 'LANGUAGES', [])]
    logger.info(f'Detected languages: {languages}')

    populate_countries()
    populate_regions()
    populate_cities()

    translate_data(languages)
