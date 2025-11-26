"""
Database population functions for populating geobank models with data.
"""
import io
import logging
import os
import zipfile

from django.core.exceptions import FieldDoesNotExist

from .constants import (
    GEONAMES_ALTERNATE_NAMES_URL,
    ISO_639_2_TO_1,
)
from .downloaders import download_heavy_file
from .models import CallingCode, City, Country, Currency, Language, Region
from .parsers import (
    parse_city_data,
    parse_country_data,
    parse_currencies_data,
    parse_flags_data,
    parse_languages_data,
    parse_region_data,
)

logger = logging.getLogger(__name__)


def populate_languages():
    """Populate Language model from restcountries API data."""
    logger.info('Populating languages...')
    
    try:
        all_languages = parse_languages_data()
        
        for code, name in all_languages.items():
            # Get the 2-letter code if it exists
            code2 = ISO_639_2_TO_1.get(code, '')
            Language.objects.update_or_create(
                code=code,
                defaults={
                    'code2': code2,
                    'name': name,
                }
            )
    except Exception as e:
        logger.error(f"Error populating languages: {e}")


def populate_currencies():
    """Populate Currency model from restcountries API data."""
    logger.info('Populating currencies...')
    
    try:
        all_currencies = parse_currencies_data()
        
        for code, info in all_currencies.items():
            Currency.objects.update_or_create(
                code=code,
                defaults={
                    'name': info['name'],
                    'symbol': info['symbol'],
                }
            )
    except Exception as e:
        logger.error(f"Error populating currencies: {e}")


def populate_countries():
    """Populate Country model and related data from geonames."""
    logger.info('Populating countries...')
    data = parse_country_data()
    
    # Build lookup maps
    currencies = {c.code: c for c in Currency.objects.all()}
    languages_map = _build_languages_map()
    
    # Store country data for neighbor processing
    country_neighbors_map = {}
    
    for item in data:
        country = _create_or_update_country(item, currencies)
        _update_calling_codes(country, item['calling_codes'])
        _assign_languages(country, item['languages'], languages_map)
        
        # Store neighbors for later processing (after all countries are created)
        if item['neighbors']:
            country_neighbors_map[item['code2']] = item['neighbors'].split(',')
    
    # Update neighbors (second pass, after all countries exist)
    _update_neighbors(country_neighbors_map)


def _build_languages_map():
    """Build a map of language codes to Language objects (both 2-letter and 3-letter)."""
    languages_map = {}
    for lang in Language.objects.all():
        languages_map[lang.code] = lang  # 3-letter code
        if lang.code2:
            languages_map[lang.code2] = lang  # 2-letter code
    return languages_map


def _create_or_update_country(item, currencies):
    """Create or update a country record."""
    # Parse population
    try:
        population = int(item['population']) if item['population'] else None
    except ValueError:
        population = None
    
    # Get currency
    currency = currencies.get(item['currency_code'])
    
    country, _ = Country.objects.update_or_create(
        geoname_id=item['geoname_id'],
        defaults={
            'name': item['name'],
            'name_ascii': item['name_ascii'],
            'fips': item['fips'],
            'continent': item['continent'],
            'population': population,
            'tld': item['tld'],
            'code2': item['code2'],
            'code3': item['code3'],
            'currency': currency,
            'postal_code_format': item['postal_code_format'],
            'postal_code_regex': item['postal_code_regex'],
        }
    )
    return country


def _update_calling_codes(country, calling_codes):
    """Update calling codes for a country."""
    country.calling_codes.all().delete()
    for code in calling_codes:
        CallingCode.objects.create(country=country, code=code)


def _assign_languages(country, languages_str, languages_map):
    """Assign languages to a country based on geonames language codes."""
    # Geonames uses 2-letter codes like "en", "ar-AE", "fa-AF"
    if languages_str:
        lang_codes = languages_str.split(',')
        country_languages = []
        for lang_code in lang_codes:
            # Language codes can be like "en-US" or "en", we want the base 2-letter code
            base_code = lang_code.split('-')[0].strip().lower()
            if base_code and base_code in languages_map:
                country_languages.append(languages_map[base_code])
        country.languages.set(country_languages)


def _update_neighbors(country_neighbors_map):
    """Update neighbor relationships for all countries."""
    logger.info('Updating country neighbors...')
    countries_by_code = {c.code2: c for c in Country.objects.all()}
    
    for country_code, neighbor_codes in country_neighbors_map.items():
        country = countries_by_code.get(country_code)
        if country:
            neighbors = []
            for neighbor_code in neighbor_codes:
                neighbor_code = neighbor_code.strip()
                if neighbor_code and neighbor_code in countries_by_code:
                    neighbors.append(countries_by_code[neighbor_code])
            country.neighbors.set(neighbors)


def populate_regions():
    """Populate Region model from geonames data."""
    logger.info('Populating regions...')
    data = parse_region_data()
    
    countries = {c.code2: c for c in Country.objects.all()}
    
    for item in data:
        country = countries.get(item['country_code'])
        if country:
            Region.objects.update_or_create(
                geoname_id=item['geoname_id'],
                defaults={
                    'name': item['name'],
                    'code': item['region_code'],
                    'name_ascii': item['name_ascii'],
                    'country': country,
                }
            )


def populate_cities(population_gte: int = 15000):
    """Populate City model from geonames data."""
    logger.info('Populating cities...')
    data = parse_city_data(population_gte)
    
    countries = {c.code2: c for c in Country.objects.all()}
    regions = {f"{r.country.code2},{r.code}": r for r in Region.objects.all()}
    
    for item in data:
        country = countries.get(item['country_code'])
        region = regions.get(f"{item['country_code']},{item['region_code']}")
        
        try:
            latitude = float(item['latitude'])
            longitude = float(item['longitude'])
        except ValueError:
            latitude = None
            longitude = None
            
        if country:
            City.objects.update_or_create(
                geoname_id=item['geoname_id'],
                defaults={
                    'name': item['name'],
                    'name_ascii': item['name_ascii'],
                    'latitude': latitude,
                    'longitude': longitude,
                    'country': country,
                    'region': region,
                    'population': item['population'],
                    'timezone': item['timezone'],
                }
            )


def populate_flags():
    """Populate flag URLs for countries from restcountries API."""
    logger.info('Populating flags...')
    
    flags_data = parse_flags_data()
    
    countries = Country.objects.all()
    for country in countries:
        country_flags = flags_data.get(country.code2)
        if country_flags:
            country.flag_png = country_flags.get("png")
            country.flag_svg = country_flags.get("svg")
            country.save(update_fields=["flag_png", "flag_svg"])


def translate_data(languages):
    """
    Translate entity names using geonames alternate names data.
    
    Args:
        languages: List of language codes to translate.
    """
    logger.info('Starting translation...')
    
    # Map geoname_id to model instance
    entities = _load_entities()
    logger.info(f'Loaded {len(entities)} entities.')

    translations = {}  # (geoname_id, lang) -> (name, is_preferred)
    tmp_file_path = None

    try:
        logger.info(f"Downloading translations from {GEONAMES_ALTERNATE_NAMES_URL}")
        tmp_file_path = download_heavy_file(GEONAMES_ALTERNATE_NAMES_URL)

        logger.info("Processing translations...")
        translations = _parse_translations(tmp_file_path, entities, languages)
        
        os.remove(tmp_file_path)
        tmp_file_path = None

        logger.info("Applying translations...")
        modified_instances = _apply_translations(translations, entities)

        logger.info("Saving translations...")
        _save_translations(modified_instances, languages)
            
    except Exception as e:
        logger.error(f"Error processing translations: {e}")
        if tmp_file_path and os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)


def _load_entities():
    """Load all translatable entities into memory."""
    logger.info('Loading entities into memory...')
    entities = {}
    for country in Country.objects.all():
        entities[country.geoname_id] = country
    for region in Region.objects.all():
        entities[region.geoname_id] = region
    for city in City.objects.all():
        entities[city.geoname_id] = city
    return entities


def _parse_translations(tmp_file_path, entities, languages):
    """Parse translations from the alternate names file."""
    translations = {}
    
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
    
    return translations


def _apply_translations(translations, entities):
    """Apply translations to entities."""
    modified_instances = set()
    
    for (geoname_id, lang), (name, _) in translations.items():
        instance = entities[geoname_id]
        field_name = f'name_{lang}'
        if hasattr(instance, field_name):
            setattr(instance, field_name, name)
            modified_instances.add(instance)
    
    return modified_instances


def _save_translations(modified_instances, languages):
    """Save translated entities to database."""
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
    
    # Ensure translation fields exist
    for lang in languages:
        for model in (Country, Region, City):
            _ensure_field(model, f"name_{lang}")

    update_fields = [f'name_{lang}' for lang in languages]
    
    if countries_to_update:
        Country.objects.bulk_update(countries_to_update, update_fields)
    if regions_to_update:
        Region.objects.bulk_update(regions_to_update, update_fields)
    if cities_to_update:
        City.objects.bulk_update(cities_to_update, update_fields)


def _ensure_field(model, field_name):
    """Ensure a field exists on a model."""
    try:
        model._meta.get_field(field_name)
    except FieldDoesNotExist:
        logger.error(f"Field '{field_name}' does not exist on {model.__name__}.")
        exit(1)
