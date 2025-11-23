from django.db import models
from django.utils.translation import gettext_lazy as _


class Country(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name=_("Name"),
    )
    name_ascii = models.CharField(
        max_length=100,
        verbose_name=_("ASCII Name"),
    )
    geoname_id = models.IntegerField(
        unique=True,
        verbose_name=_("Geoname ID"),
    )
    continent = models.CharField(
        max_length=50,
        verbose_name=_("Continent"),
    )
    code2 = models.CharField(
        max_length=2,
        unique=True,
        verbose_name=_("ISO Alpha-2 Code"),
    )
    code3 = models.CharField(
        max_length=3,
        unique=True,
        verbose_name=_("ISO Alpha-3 Code"),
    )
    postal_code_format = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_("Postal Code Format"),
    )
    postal_code_regex = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Postal Code Regex"),
    )
    flag_png = models.URLField(
        max_length=500, blank=True, null=True, verbose_name=_("Flag PNG URL")
    )
    flag_svg = models.URLField(
        max_length=500, blank=True, null=True, verbose_name=_("Flag PNG URL")
    )
    is_active = models.BooleanField(
        default=True, verbose_name=_("Is Active")
    )

    class Meta:
        verbose_name = _("Country")
        verbose_name_plural = _("Countries")


class CallingCode(models.Model):
    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name='calling_codes',
        verbose_name=_("Country"),
    )
    code = models.CharField(
        max_length=20,
        verbose_name=_("Code"),
    )

    class Meta:
        verbose_name = _("Calling Code")
        verbose_name_plural = _("Calling Codes")


class Region(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name=_("Name"),
    )
    name_ascii = models.CharField(
        max_length=100,
        verbose_name=_("ASCII Name"),
    )
    geoname_id = models.IntegerField(
        unique=True,
        verbose_name=_("Geoname ID"),
    )
    code = models.CharField(
        max_length=10,
        verbose_name=_("Code"),
    )
    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name='regions',
        verbose_name=_("Country"),
    )
    is_active = models.BooleanField(
        default=True, verbose_name=_("Is Active")
    )

    class Meta:
        verbose_name = _("Region")
        verbose_name_plural = _("Regions")
        unique_together = ("country", "code", )


class City(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name=_("Name"),
    )
    name_ascii = models.CharField(
        max_length=100,
        verbose_name=_("ASCII Name"),
    )
    geoname_id = models.IntegerField(
        unique=True,
        verbose_name=_("Geoname ID"),
    )
    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name='cities',
        verbose_name=_("Country"),
    )
    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name='cities',
        verbose_name=_("Region"),
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(
        default=True, verbose_name=_("Is Active")
    )

    class Meta:
        verbose_name = _("City")
        verbose_name_plural = _("Cities")
