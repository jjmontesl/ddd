# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

from collections import defaultdict, namedtuple
import logging
import math
import random
import sys


import json
import requests
import os
from ddd.ddd import ddd


# Get instance of logger for this module
logger = logging.getLogger(__name__)

class WMSClient():
    """
    """

    def __init__(self, name, url, width=850, height=600):
        self.name = name
        self.url = url
        self.width = width
        self.height = height
        self.url = "http://localhost:8080/service?LAYERS=ign_ortho&FORMAT=image/jpeg&SRS=EPSG:3857&SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&STYLES=&BBOX={bbox}&WIDTH={width}&HEIGHT={height}"

    def request(self, params):

        #output = {"type":"FeatureCollection","features":[]}

        url = self.url
        for k, v in params.items():
            url = url.replace('{' + k + '}', v)

        print("Requesting: %s" % url)
        r = requests.get(url)
        return r

        '''
        data_length = len(data['features'])
        for f in data['features']:
            output['features'].append(f)
        while data_length == 1000:
            link = r.links['next']['url']
            r = requests.get(link)
            data = r.json()
            for f in data['features']:
                output['features'].append(f)
            print(len(output['features']))
            data_length = len(data['features'])
        with open('data.geojson', 'w') as outfile:
            json.dump(output, outfile)
        '''

    def request_image(self, bbox):
        """
            Example WMS URL: http://localhost:8080/service?LAYERS=osm_standard&FORMAT=image/jpeg&SRS=EPSG:3857&SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&STYLES=&BBOX={bbox}&WIDTH=850&HEIGHT=600
        """

        bbox = ",".join(["%f" % c for c in bbox])
        filename = "_cache/images/wms/%s-%s.jpg" % (self.name, bbox)
        if os.path.exists(filename): return

        r = self.request({'bbox': bbox,
                          'name': str(self.name),
                          'width': str(self.width),
                          'height': str(self.height)})
        data = r.content
        with open(filename, "wb") as f:
            f.write(data)

        return data

    def image_textured(self, bbox):

        # TODO: Reuse most of this (material, plane, etc)

        bbox = ",".join(["%f" % c for c in bbox])
        filename = "_cache/images/wms/%s-%s.jpg" % (self.name, bbox)

        material = ddd.material(texture_path=filename)

        plane = ddd.rect(name="WMS Image (%s)" % self.name).triangulate().material(material)
        plane = ddd.uv.map_cubic(plane)
        plane = plane.recenter()
        plane = plane.rotate(ddd.ROT_FLOOR_TO_FRONT)

        return plane


if __name__ == '__main__':

    client = WMSClient("es_ortho", url=None, width=512, height=512)
    bbox = [-1007960.7600516, 5131958.1924932, -878017.81196677, 5223682.6264354]
    data = client.request_image(bbox)





