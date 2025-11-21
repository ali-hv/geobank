from django.db import models
from django.utils.translation import gettext_lazy as _


class Country(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name=_("Name")
    )
    name_ascii = models.CharField(
        max_length=100,
        verbose_name=_("ASCII Name")
    )
    geoname_id = models.IntegerField(
        unique=True,
        verbose_name=_("Geoname ID")
    )
    continent = models.CharField(
        max_length=50,
        verbose_name=_("Continent")
    )
    code2 = models.CharField(
        max_length=2,
        unique=True,
        verbose_name=_("ISO Alpha-2 Code")
    )
    code3 = models.CharField(
        max_length=3,
        unique=True,
        verbose_name=_("ISO Alpha-3 Code")
    )
    calling_code = models.CharField(
        max_length=10,
        verbose_name=_("Calling Code")
    )
    postal_code_format = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_("Postal Code Format")
    )
    postal_code_regex = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Postal Code Regex")
    )
    flag = models.ImageField(
        upload_to='flags/',
        null=True,
        blank=True,
        verbose_name=_("Flag")
    )

    class Meta:
        verbose_name = _("Country")
        verbose_name_plural = _("Countries")


class Region(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name=_("Name")
    )
    name_ascii = models.CharField(
        max_length=100,
        verbose_name=_("ASCII Name")
    )
    geoname_id = models.IntegerField(
        unique=True,
        verbose_name=_("Geoname ID")
    )
    code = models.CharField(
        max_length=10,
        verbose_name=_("Code")
    )
    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name='regions',
        verbose_name=_("Country")
    )

    class Meta:
        verbose_name = _("Region")
        verbose_name_plural = _("Regions")


class City(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name=_("Name")
    )
    name_ascii = models.CharField(
        max_length=100,
        verbose_name=_("ASCII Name")
    )
    geoname_id = models.IntegerField(
        unique=True,
        verbose_name=_("Geoname ID")
    )
    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name='cities',
        verbose_name=_("Country")
    )
    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name='cities',
        verbose_name=_("Region")
    )

    class Meta:
        verbose_name = _("City")
        verbose_name_plural = _("Cities")
