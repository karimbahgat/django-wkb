from django.forms.widgets import HiddenInput
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.db import models
from django import forms

import json

try:
    from leaflet.forms.widgets import LeafletWidget
    HAS_LEAFLET = True
except ImportError:
    HAS_LEAFLET = False

from .geometry import WKBGeometry


class WKBFormField(forms.Field):
    widget = LeafletWidget if HAS_LEAFLET else HiddenInput

    def __init__(self, *args, **kwargs):
        if not HAS_LEAFLET:
            import warnings
            warnings.warn('`django-leaflet` is not available.')
        geom_type = kwargs.pop('geom_type')
        #kwargs.setdefault('validators', [WKBValidator(geom_type)])
        super(WKBFormField, self).__init__(*args, **kwargs)


# https://docs.djangoproject.com/en/3.1/howto/custom-model-fields/

class WKBField(models.BinaryField):
    description = _("Geometry as WKB")
    #form_class = WKBFormField
    dim = 2
    geom_type = 'GEOMETRY'
    editable = True

    def formfield(self, **kwargs):
        kwargs.setdefault('geom_type', self.geom_type)
        return super(WKBField, self).formfield(**kwargs)

    def from_db_value(self, value, expression, connection):
        # used by db loading
        if value is None:
            return value

        return WKBGeometry(value)

    def to_python(self, value):
        # used by deserialization and form cleaning
        value = super(WKBField, self).to_python(value)
        
        if isinstance(value, WKBGeometry):
            return value

        if value is None:
            return value

        return WKBGeometry(value)

    def get_db_prep_value(self, value, connection, prepared=False):
        # used on db insert
        if isinstance(value, str):
            # GeoJSON string
            value = json.loads(value)
        if isinstance(value, dict):
            # GeoJSON dict, serialize to WKB
            value = WKBGeometry.from_geojson(value)
        value = super(WKBField, self).get_db_prep_value(value, connection, prepared)
        return value



class GeometryField(WKBField):
    pass


class GeometryCollectionField(GeometryField):
    geom_type = 'GEOMETRYCOLLECTION'


class PointField(GeometryField):
    geom_type = 'POINT'


class MultiPointField(GeometryField):
    geom_type = 'MULTIPOINT'


class LineStringField(GeometryField):
    geom_type = 'LINESTRING'


class MultiLineStringField(GeometryField):
    geom_type = 'MULTILINESTRING'


class PolygonField(GeometryField):
    geom_type = 'POLYGON'


class MultiPolygonField(GeometryField):
    geom_type = 'MULTIPOLYGON'


    
