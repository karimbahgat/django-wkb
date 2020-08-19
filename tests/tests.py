# Most of the tests in this file are adapted from django-geosjon
# https://github.com/makinacorpus/django-geojson/blob/master/djgeojson/tests.py

from django.test import TestCase
from django.template import Template, Context
from django.db import transaction
from django.core import serializers
from django.core.exceptions import ValidationError, SuspiciousOperation

import json

from djangowkb.geometry import WKBGeometry
from djangowkb.fields import WKBField, WKBFormField, HAS_LEAFLET

from .models import Address, CountryDivision
from .forms import AddressForm


# Create your tests here.
class RealWordTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        pass
    
    def test_example(self):
        DEBUG = False
        PROFILE = False
        
        print('loading')
        import sys
        #sys.path.append(r'C:\Users\kimok\OneDrive\Documents\GitHub\pyshp')
        import shapefile
        r = shapefile.Reader(r"C:\Users\kimok\Downloads\ne_10m_admin_1_states_provinces (1)\ne_10m_admin_1_states_provinces.shp")
        #r = shapefile.Reader(r"C:\Users\kimok\Desktop\BIGDATA\gazetteer data\raw\global_settlement_points_v1.01.shp", encoding='latin')
        #r = shapefile.Reader(r"C:\Users\kimok\Desktop\BIGDATA\gazetteer data\raw\global_urban_extent_polygons_v1.01.shp")
        shapes = r.shapes()
        items = [shape.__geo_interface__ for shape in shapes] # items = [(i+1, f.bbox) for i,f in enumerate(d)]
        print(len(items))

        #####################

        # build
        print('inserting models with wkb field data')
        if PROFILE:
            import cProfile
            prof = cProfile.Profile()
            prof.enable()

        with transaction.atomic():
            items = (CountryDivision(name='TestName',geom=item) for item in items)
            CountryDivision.objects.bulk_create(items)
            #for item in items:
            #    inst = CountryDivision.objects.create(name='TestName', geom=item)
        
        if PROFILE:
            print(prof.print_stats('cumtime'))
            #fdsdfd

        print('inserted',CountryDivision.objects.all().count())

        for obj in CountryDivision.objects.all()[:10]:
            print('fetch example',repr(obj.geom))
            geoj = obj.geom.__geo_interface__
            print('geojson',str(geoj)[:100])
            print('bbox',obj.geom.bbox())

        self.assertTrue(True)

#####

class BaseWKBGeometryTest(object):

    def test_wkb_is_valid(self):
        from shapely.wkb import loads
        self.assertTrue(bool(loads(self.geom.wkb)))

    def test_geom_type(self):
        self.assertEquals(self.geom.geom_type, self.geom_type)

    def test_bbox(self):
        self.assertEquals(self.geom.bbox(), self.bbox)

    def test_geo_interface(self):
        self.assertDictEqual(self.geom.__geo_interface__, self.geoj)

    def test_geojson(self):
        self.assertJSONEqual(self.geom.geojson, json.dumps(self.geoj))

class PointWKBGeometryTest(BaseWKBGeometryTest, TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.geoj = {'type': 'Point', 'coordinates': (0.0, 0.0)}
        cls.bbox = (0.0,0.0,0.0,0.0)
        cls.geom_type = cls.geoj['type']
        cls.geom = WKBGeometry(cls.geoj)

class LineStringWKBGeometryTest(BaseWKBGeometryTest, TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.geoj = {'type': 'LineString', 'coordinates': ((0.0, 0.0),(1.0,1.0),(2.0,2.0))}
        cls.bbox = (0.0,0.0,2.0,2.0)
        cls.geom_type = cls.geoj['type']
        cls.geom = WKBGeometry(cls.geoj)

class PolygonWKBGeometryTest(BaseWKBGeometryTest, TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.geoj = {'type': 'Polygon', 'coordinates': (((0.0, 0.0),(0.0,2.0),(2.0,2.0),(2.0,0.0),(0.0,0.0)),
                                                       ((0.25,0.25),(0.75,0.25),(0.75,0.75),(0.25,0.75),(0.25,0.25)))}
        cls.bbox = (0.0,0.0,2.0,2.0)
        cls.geom_type = cls.geoj['type']
        cls.geom = WKBGeometry(cls.geoj)

class MultiPointWKBGeometryTest(BaseWKBGeometryTest, TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.geoj = {'type': 'MultiPoint', 'coordinates': ((0.0, 0.0),(1.0, 1.0))}
        cls.bbox = (0.0,0.0,1.0,1.0)
        cls.geom_type = cls.geoj['type']
        cls.geom = WKBGeometry(cls.geoj)

class MultiLineStringWKBGeometryTest(BaseWKBGeometryTest, TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.geoj = {'type': 'MultiLineString', 'coordinates': (((0.0, 0.0),(0.0,2.0),(2.0,2.0),(2.0,0.0),(0.0,0.0)),
                                                               ((0.25,0.25),(0.75,0.25),(0.75,0.75),(0.25,0.75),(0.25,0.25)))}
        cls.bbox = (0.0,0.0,2.0,2.0)
        cls.geom_type = cls.geoj['type']
        cls.geom = WKBGeometry(cls.geoj)

class MultiPolygonWKBGeometryTest(BaseWKBGeometryTest, TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.geoj = {'type': 'MultiPolygon', 'coordinates': [(((0.0, 0.0),(0.0,2.0),(2.0,2.0),(2.0,0.0),(0.0,0.0)),),
                                                            (((10.25,10.25),(10.75,10.25),(10.75,10.75),(10.25,10.75),(10.25,10.25)),)]
                    }
        cls.bbox = (0.0,0.0,10.75,10.75)
        cls.geom_type = cls.geoj['type']
        cls.geom = WKBGeometry(cls.geoj)

#####

class BaseModelFieldTest(object):

    def test_field_value_is_wkbgeometry(self):
        self.assertIsInstance(self.address.geom, WKBGeometry)

    def test_field_value_accepts_geojson_dict(self):
        pass

    def test_field_value_accepts_geojson_string(self):
        pass

    def test_field_value_accepts_wkbgeometry(self):
        pass

    def test_model_can_save(self):
        pass

    def test_model_can_create(self):
        pass

    def test_model_can_bulk_create(self):
        pass

    def test_form_field_default_is_wkbfield(self):
        field = self.address._meta.get_field('geom').formfield()
        self.assertIsInstance(field, WKBFormField)

    def test_form_field_widget_default_is_leaflet(self):
        if HAS_LEAFLET:
            from djangowkb.fields import LeafletWidget
            field = self.address._meta.get_field('geom').formfield()
            self.assertIsInstance(field.widget, LeafletWidget)

    def test_form_field_widget_renders_as_map(self):
##        client = Client()
##        url = reverse('index')
##        response = self.client.get(url)
##        self.assertEqual(response.status_code, 200)
##        self.assertTemplateUsed(response, 'index.html')
##        self.assertContains(response, 'Company Name XYZ')
        inst = self.address
        form = AddressForm(instance=inst)
        #raise Exception(repr(inst.geom))
        #raise Exception(repr(form.geom))
        #raise Exception(form.as_p())
        templ = Template('''
{% load leaflet_tags %}

{% block page_content %}

{% block extra_assets %}
   {% leaflet_js plugins="forms" %}
   {% leaflet_css plugins="forms" %}
{% endblock %}

<h1>Map Test Template</h1>

<div id="map_container">
{{ form }}
</div>

{% endblock %}
''')
        context = Context({'form':form})
        html = templ.render(context) + ''
##        from django.utils.safestring import mark_safe
##        html = mark_safe(html)
##        raise Exception(html)
##        #raise Exception(type(html))
##        textarea_tag = html.index('<textarea id="id_geom"')
##        start = html.index('>', textarea_tag) + 1
##        end = html.index('<', start)
##        textarea_content = html[start:end]
##        from django.utils.html import escape,unquote
##        raise Exception(textarea_content)
##        geojson = inst.geom.geojson
##        self.assertEquals(textarea_content, geojson)
##        self.assertContains(html, geojson)
        self.assertIn('<textarea id="id_geom"', html)
        self.assertIn('map = L.Map.', html)

    # below is adapted

    def test_models_can_have_geojson_fields(self):
        saved = Address.objects.get(id=self.address.id)
        self.assertEqual(saved.geom.wkb, self.address.geom.wkb)
##        if isinstance(saved.geom, dict):
##            self.assertDictEqual(saved.geom, self.address.geom)
##        else:
##            # Django 1.8 !
##            self.assertEqual(json.loads(saved.geom.geojson), self.address.geom)

##    def test_default_form_field_has_geojson_validator(self):
##        field = self.address._meta.get_field('geom').formfield()
##        validator = field.validators[0]
##        self.assertTrue(isinstance(validator, GeoJSONValidator))

    def test_form_field_raises_if_wrong_value(self):
        field = self.address._meta.get_field('geom').formfield()
        self.assertRaises(ValidationError, field.clean,
                          1.0)

    def test_form_field_raises_if_type_missing(self):
        field = self.address._meta.get_field('geom').formfield()
        self.assertRaises(ValidationError, field.clean,
                          {'foo': 'bar'})

    def test_form_field_raises_if_invalid_type(self):
        field = self.address._meta.get_field('geom').formfield()
        #raise ValidationError(field.clean({'type': 'FeatureCollection', 'foo': 'bar'}))
        self.assertRaises(ValidationError, field.clean,
                          {'type': 'FeatureCollection', 'foo': 'bar'})

##    def test_field_can_be_serialized(self):
##        serializer = Serializer()
##        geojson = serializer.serialize(Address.objects.all(), crs=False)
##        features = json.loads(geojson)
##        self.assertEqual(
##            features, {
##                'type': u'FeatureCollection',
##                'features': [{
##                    'id': self.address.id,
##                    'type': 'Feature',
##                    'geometry': {'type': 'Point', 'coordinates': [0, 0]},
##                    'properties': {
##                        'model': 'djgeojson.address'
##                    }
##                }]
##            })

##    def test_field_can_be_deserialized(self):
##        input_geojson = """
##        {"type": "FeatureCollection",
##         "features": [
##            { "type": "Feature",
##                "properties": {"model": "djgeojson.address"},
##                "id": 1,
##                "geometry": {
##                    "type": "Point",
##                    "coordinates": [0.0, 0.0]
##                }
##            }
##        ]}"""
##        objects = list(serializers.deserialize('geojson', input_geojson))
##        self.assertEqual(objects[0].object.geom,
##                         {'type': 'Point', 'coordinates': [0, 0]})

##    def test_model_can_be_omitted(self):
##        serializer = Serializer()
##        geojson = serializer.serialize(Address.objects.all(),
##                                       with_modelname=False)
##        features = json.loads(geojson)
##        self.assertEqual(
##            features, {
##                "crs": {
##                    "type": "link",
##                    "properties": {
##                        "href": "http://spatialreference.org/ref/epsg/4326/",
##                        "type": "proj4"
##                    }
##                },
##                'type': 'FeatureCollection',
##                'features': [{
##                    'id': self.address.id,
##                    'type': 'Feature',
##                    'geometry': {'type': 'Point', 'coordinates': [0, 0]},
##                    'properties': {}
##                }]
##            })

# MAYBE ACTUALLY JUST HAVE A SEPARATE INIT CLASS, WITH METHODS FOR DIFFERENT INIT TYPES...

class ModelFieldFromWKBTest(BaseModelFieldTest, TestCase):
    
    @classmethod
    def setUpTestData(cls):
        wkb = WKBGeometry({'type': 'Point', 'coordinates': [0, 0]}).wkb
        geom = WKBGeometry(wkb)
        cls.address = Address.objects.create(geom=geom)

class ModelFieldFromGeoJSONDictTest(BaseModelFieldTest, TestCase):
    
    @classmethod
    def setUpTestData(cls):
        geoj = {'type': 'Point', 'coordinates': [0, 0]}
        geom = WKBGeometry(geoj)
        cls.address = Address.objects.create(geom=geom)
        
class ModelFieldFromGeoJSONStringTest(BaseModelFieldTest, TestCase):
    
    @classmethod
    def setUpTestData(cls):
        json_string = json.dumps({'type': 'Point', 'coordinates': [0, 0]})
        geom = WKBGeometry(json_string)
        cls.address = Address.objects.create(geom=geom)

            
