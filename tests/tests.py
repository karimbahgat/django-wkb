from django.test import TestCase
from django.db import transaction
from .models import CountryDivision



# Create your tests here.
class BasicTestCase(TestCase):

    def setUp(self):
        pass
    
    def test_example(self):
        DEBUG = False
        PROFILE = False
        
        print('loading')
        import sys
        sys.path.append(r'C:\Users\kimok\OneDrive\Documents\GitHub\pyshp')
        import shapefile
        r = shapefile.Reader(r"C:\Users\kimok\Downloads\ne_10m_admin_1_states_provinces (1)\ne_10m_admin_1_states_provinces.shp")
        #r = shapefile.Reader(r"C:\Users\kimok\Desktop\BIGDATA\gazetteer data\raw\global_settlement_points_v1.01.shp", encoding='latin')
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

        for obj in CountryDivision.objects.all()[:2]:
            print('fetch example',repr(obj.geom))
            geoj = obj.geom.__geo_interface__
            print('geojson',str(geoj)[:100])
            print('bbox',obj.geom.bbox())



            
