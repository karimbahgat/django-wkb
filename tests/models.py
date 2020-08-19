from django.db import models

from djangowkb.fields import WKBField

class CountryDivision(models.Model):
    name = models.CharField(max_length=20)
    geom = WKBField()

class Address(models.Model):
    geom = WKBField()


