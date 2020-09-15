from django.db import models

from djangowkb.fields import GeometryField

class CountryDivision(models.Model):
    name = models.CharField(max_length=20)
    geom = GeometryField()

class Address(models.Model):
    geom = GeometryField()


