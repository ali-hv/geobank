"""
Utility functions for populating geobank data.

This module provides the main entry point for populating the geobank database
with geographic data from external sources (geonames.org, restcountries.com).
"""
import logging

from django.conf import settings

from .populators import (
    populate_cities,
    populate_countries,
    populate_currencies,
    populate_flags,
    populate_languages,
    populate_regions,
    translate_data,
)

logger = logging.getLogger(__name__)


def populate_geobank_data(population_gte: int = 15000):
    """
    Populate all geobank data from external sources.
    
    This function orchestrates the entire data population process:
    1. Populates reference data (languages, currencies)
    2. Populates geographic data (countries, regions, cities)
    3. Populates supplementary data (flags)
    4. Applies translations based on configured languages
    
    Args:
        population_gte: Minimum population threshold for cities.
                       Common values: 500, 1000, 5000, 15000
    """
    # Get configured languages for translation
    languages = [lang[0] for lang in getattr(settings, 'LANGUAGES', [])]
    logger.info(f'Detected languages: {languages}')

    # Populate reference data first (languages, currencies)
    # These are needed before populating countries
    populate_languages()
    populate_currencies()
    
    # Populate geographic data
    populate_countries()
    populate_regions()
    populate_cities(population_gte)

    # Populate supplementary data
    populate_flags()
    
    # Apply translations
    translate_data(languages)
    
    logger.info('Geobank data population complete.')


# Re-export individual functions for granular control
__all__ = [
    'populate_geobank_data',
    'populate_languages',
    'populate_currencies',
    'populate_countries',
    'populate_regions',
    'populate_cities',
    'populate_flags',
    'translate_data',
]
