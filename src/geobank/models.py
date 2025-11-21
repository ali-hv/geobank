from django.db import models
from django.utils.translation import gettext_lazy as _


class Country(models.Model):
    name = models.CharField(max_length=100)
    name_ascii = models.CharField(max_length=100)
    geoname_id = models.IntegerField(unique=True)
    continent = models.CharField(max_length=50)
    code2 = models.CharField(max_length=2, unique=True)
    code3 = models.CharField(max_length=3, unique=True)
    calling_code = models.CharField(max_length=10)
    postal_code_format = models.CharField(max_length=100, null=True, blank=True)
    postal_code_regex = models.CharField(max_length=255, null=True, blank=True)
    flag = models.ImageField(upload_to='flags/', null=True, blank=True)

    class Meta:
        verbose_name = _("Country")
        verbose_name_plural = _("Countries")


class Region(models.Model):
    name = models.CharField(max_length=100)
    name_ascii = models.CharField(max_length=100)
    geoname_id = models.IntegerField(unique=True)
    code = models.CharField(max_length=10, unique=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='regions')

    class Meta:
        verbose_name = _("Region")
        verbose_name_plural = _("Regions")


class City(models.Model):
    name = models.CharField(max_length=100)
    name_ascii = models.CharField(max_length=100)
    geoname_id = models.IntegerField(unique=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='cities')
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='cities')

    class Meta:
        verbose_name = _("City")
        verbose_name_plural = _("Cities")
