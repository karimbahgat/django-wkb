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

    def __init__(self, wkb, srid=None):
        self.srid = srid
        self.wkb = wkb

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
    def from_geojson(geojson):
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
            num = len(parts)
            vals.append(num)
            fmt = 'i'
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
                    vals.extend(geojson['coordinates'])
                    fmt += 'dd'
                elif 'LineString' in typ:
                    fmt += writepoly(geojson['coordinates'])
                elif 'Polygon' in typ:
                    for poly in geojson['coordinates']:
                        fmt += writepoly(poly)
            return fmt

        #stream = BytesIO(self.wkb)
        vals = []
        fmt = ''

        # byteorder
        byteorder = '<'
        fmt += byteorder
        vals.append(1) # little endian
        fmt += 'b'

        # type
        typ = geojson['type']
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
            fmt += multi(geojson['coordinates'], typ)
        else:
            raise NotImplementedError('Geometry type {}'.format(typ))

        wkb = pack(fmt, *vals)
        return WKBGeometry(wkb)

    @property
    def geom_type(self):
        byteorder = _wkb_byteorder(self.wkb)
        typ = unpack_from(byteorder+'xi', self.wkb)[0]
        typ = wkbtype_to_shptype[typ]
        return typ

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

    
