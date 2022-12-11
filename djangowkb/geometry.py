# contains the geometry wrapper return value for WKBField

from struct import unpack, unpack_from, pack
from io import BytesIO
from itertools import islice,chain
import json


def _wkb_byteorder(wkb):
    byteorder = unpack_from('b', wkb)[0]
    byteorder = '>' if byteorder == 0 else '<'
    return byteorder


wkbtype_to_shptype = {1: 'Point',
                      2: 'LineString',
                      3: 'Polygon',
                      4: 'MultiPoint',
                      5: 'MultiLineString',
                      6: 'MultiPolygon',
                      7: 'GeometryCollection'}

shptype_to_wkbtype = {'Point': 1,
                      'LineString': 2,
                      'Polygon': 3,
                      'MultiPoint': 4,
                      'MultiLineString': 5,
                      'MultiPolygon': 6,
                      'GeometryCollection': 7}


class WKBGeometry(object):

    def __init__(self, geo_input, srid=None):
        if isinstance(geo_input, bytes):
            wkb = geo_input
        elif isinstance(geo_input, dict):
            geom = WKBGeometry.from_geojson_dict(geo_input)
            wkb = geom.wkb
        elif isinstance(geo_input, str):
            geom = WKBGeometry.from_geojson(geo_input)
            wkb = geom.wkb
        else:
            raise ValueError('WKBGeometry input value must be a wkb bytes object, a GeoJSON dict, or GeoJSON string, not {}'.format(geo_input))
        self.wkb = wkb
        self.srid = srid

    @property
    def __geo_interface__(self):
        from shapely.wkb import loads as wkb_loads
        shp = wkb_loads(self.wkb)
        geoj = shp.__geo_interface__
        return geoj

    @property
    def geojson(self):
        json_string = json.dumps(self.__geo_interface__)
        return json_string

    @staticmethod
    def from_geojson(geojson_string):
        geojson_dict = json.loads(geojson_string)
        geom = WKBGeometry.from_geojson_dict(geojson_dict)
        return geom

    @staticmethod
    def from_geojson_dict(geojson):
        # shapely
        #from shapely.geometry import asShape
        #wkb = asShape(geojson).wkb
        #return wkb

        # geomet
        #from geomet.wkb import dumps
        #wkb = dumps(geojson)
        #return wkb
        
        # custom
        def writering(ring):#, stream):
            pnum = len(ring)
            vals.append(pnum)
            #vals.extend((xy for p in ring for xy in p))
            vals.extend(chain.from_iterable(ring))
            return 'i{}d'.format(pnum*2)
        
        def writepoly(poly):#, stream):
            num = len(poly)
            vals.append(num)
            fmt = 'i'
            for ring in poly:
                fmt += writering(ring)
            return fmt

        def multi(parts, typ):
            # number of multi parts
            num = len(parts)
            vals.append(num)
            fmt = 'i'
            # iter parts
            for part in parts:
                # byteorder
                vals.append(1) # little endian
                fmt += 'b'
                # type
                wkbtyp = shptype_to_wkbtype[typ]
                vals.append(wkbtyp)
                fmt += 'i'
                # coords
                if 'Point' in typ:
                    vals.extend(part)
                    fmt += 'dd'
                elif 'LineString' in typ:
                    fmt += writering(part)
                elif 'Polygon' in typ:
                    fmt += writepoly(part)
            return fmt

        # first validate
        if not isinstance(geojson, dict):
            raise TypeError('Geojson must be a dict mapping, not {}'.format(geojson))

        #stream = BytesIO(self.wkb)
        vals = []
        fmt = ''

        # byteorder
        byteorder = '<'
        fmt += byteorder
        vals.append(1) # little endian
        fmt += 'b'

        # type
        if not 'type' in geojson:
            raise ValueError('GeoJSON geometry is missing the "type" key'.format(geojson))
        typ = geojson['type']
        if not typ in shptype_to_wkbtype:
            raise ValueError('{} is not a valid GeoJSON geometry type'.format(typ))
        #if typ != 'coordinates' not in geojson:
        #    raise Exception('GeoJSON geometry {} is missing the "coordinates" key'.format(geojson))
        wkbtyp = shptype_to_wkbtype[typ]
        vals.append(wkbtyp)
        fmt += 'i'

        # contents
        if typ == 'Point':
            vals.extend(geojson['coordinates'])
            fmt += 'dd'
        elif typ == 'LineString':
            fmt += writering(geojson['coordinates'])
        elif typ == 'Polygon':
            fmt += writepoly(geojson['coordinates'])
        elif 'Multi' in typ:
            fmt += multi(geojson['coordinates'], typ.replace('Multi',''))
        else:
            raise NotImplementedError('Geometry type {} not yet supported'.format(typ))

        wkb = pack(fmt, *vals)
        return WKBGeometry(wkb)

    @property
    def geom_type(self):
        byteorder = _wkb_byteorder(self.wkb)
        typ = unpack_from(byteorder+'xi', self.wkb)[0]
        typ = wkbtype_to_shptype[typ]
        return typ

    # def iter_coords(self):
    #     # not finished
    #     # can maybe be reused for geo interface... 
    #     stream = BytesIO(self.wkb)
    #     byteorder = _wkb_byteorder(stream.read(1))
    #     wkbtyp = unpack(byteorder+'i', stream.read(4))[0]
    #     typ = wkbtype_to_shptype[wkbtyp]
    #     if typ == 'Point':
    #         xy = unpack(byteorder+'dd', stream.read(8*2))
    #         yield xy
    #     elif typ == 'LineString':
    #         coords = getring(stream)
    #         yield coords
    #     elif typ == 'Polygon':
    #         for coords in getpoly(stream):
    #             yield coords
    #     elif typ == 'MultiPoint':
    #         num = unpack(byteorder+'i', stream.read(4))[0]
    #         flat = unpack(byteorder+'5xdd'*(num), stream.read((5+16)*num))
    #         xs,ys = islice(flat,0,None,2), islice(flat,1,None,2)
    #         coords = zip(xs,ys)
    #         yield coords
    #     elif typ == 'MultiLineString':
    #         num = unpack(byteorder+'i', stream.read(4))[0]
    #         for _ in range(num):
    #             coords = getring(multi(stream))
    #             yield coords
    #     elif typ == 'MultiLineString':
    #         num = unpack(byteorder+'i', stream.read(4))[0]
    #         for _ in range(num):
    #             for coords in getring(multi(stream)):
    #                 yield coords

    def bbox(self):
        # real is below...
        def ringbox(stream):
            pnum = unpack(byteorder+'i', stream.read(4))[0]
            flat = unpack(byteorder+'{}d'.format(pnum*2), stream.read(16*pnum))
            #xs,ys = flat[0::2],flat[1::2]
            #return min(xs),min(ys),max(xs),max(ys)
            return (min(islice(flat,0,None,2)),
                    min(islice(flat,1,None,2)),
                    max(islice(flat,0,None,2)),
                    max(islice(flat,1,None,2)) )
        
        def polybox(stream):
            # only check exterior, ie the first ring
            #print 'poly tell',stream.tell()
            num = unpack(byteorder+'i', stream.read(4))[0]
            xmin,ymin,xmax,ymax = ringbox(stream)
            # skip holes, ie remaining rings
            if num > 1:
                for _ in range(num-1):
                    pnum = unpack(byteorder+'i', stream.read(4))[0]
                    unpack(byteorder+'{}x'.format(pnum*2*8), stream.read(16*pnum))
            return xmin,ymin,xmax,ymax
        
        def multi(stream):
            # 1 byte and one 4bit int class type of 1,2,3: point line or poly
            stream.read(5)
            return stream

        stream = BytesIO(self.wkb)
        byteorder = _wkb_byteorder(stream.read(1))
        wkbtyp = unpack(byteorder+'i', stream.read(4))[0]
        typ = wkbtype_to_shptype[wkbtyp]
        if typ == 'Point':
            x,y = unpack(byteorder+'dd', stream.read(8*2))
            xmin = xmax = x
            ymin = ymax = y
        elif typ == 'LineString':
            xmin,ymin,xmax,ymax = ringbox(stream)
        elif typ == 'Polygon':
            xmin,ymin,xmax,ymax = polybox(stream)
        elif typ == 'MultiPoint':
            num = unpack(byteorder+'i', stream.read(4))[0]
            flat = unpack(byteorder+'5xdd'*(num), stream.read((5+16)*num))
            xmin,ymin,xmax,ymax = (min(islice(flat,0,None,2)),
                                    min(islice(flat,1,None,2)),
                                    max(islice(flat,0,None,2)),
                                    max(islice(flat,1,None,2)) )
        elif typ == 'MultiLineString':
            num = unpack(byteorder+'i', stream.read(4))[0]
            xmins,ymins,xmaxs,ymaxs = zip(*(ringbox(multi(stream)) for _ in range(num)))
            xmin,ymin,xmax,ymax = min(xmins),min(ymins),max(xmaxs),max(ymaxs)
        elif typ == 'MultiPolygon':
            num = unpack(byteorder+'i', stream.read(4))[0]
            xmins,ymins,xmaxs,ymaxs = zip(*(polybox(multi(stream)) for _ in range(num)))
            xmin,ymin,xmax,ymax = min(xmins),min(ymins),max(xmaxs),max(ymaxs)
        else:
            raise NotImplementedError('Geometry bbox calculation of type {}'.format(typ))

        return xmin,ymin,xmax,ymax

    
