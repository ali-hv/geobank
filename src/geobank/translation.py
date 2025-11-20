from modeltranslation.translator import register, TranslationOptions
from .models import Country, City, Region

@register(Country)
class CountryTranslationOptions(TranslationOptions):
    fields = ('name',)

@register(City)
class CityTranslationOptions(TranslationOptions):
    fields = ('name',)

@register(Region)
class RegionTranslationOptions(TranslationOptions):
    fields = ('name',)
