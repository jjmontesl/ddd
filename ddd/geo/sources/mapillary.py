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

class MapillaryClient():

    url_api = 'https://a.mapillary.com/v3/'
    url_images = 'https://images.mapillary.com/'

    def __init__(self, client_id):
        self.client_id = client_id

    def request(self, method, params):

        #output = {"type":"FeatureCollection","features":[]}

        url = self.url_api + method + ('?client_id={}').format(self.client_id)
        for k, v in params.items():
            url = url + "&%s=%s" % (k, v)

        print("Requesting: %s" % url)
        r = requests.get(url)
        data = r.json()

        return data

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

    def images_list(self, coords, limit=5, radius=100):
        data = self.request("images", {'closeto': "%.6f,%.6f" % (coords[0], coords[1]), 'radius': radius, 'per_page': limit})

        #print(json.dumps(data, indent=4))

        for feature in data['features']:
            key = feature['properties']['key']
            pano = feature['properties']['pano']
            camera_angle = feature['properties']['ca']
            geom = feature['geometry']
            #obj = ddd.geometry(geom)
            #print("Image: %s  CameraAngle: %s  Pano: %s  Geom: %s" % (key, camera_angle, pano, geom))

        return data

    def image_textured(self, feature):
        key = feature['properties']['key']
        filename = "_cache/images/mapillary/%s-%s.jpg" % (key, 1024)
        material = ddd.material(texture_path=filename)

        plane = ddd.rect(name="Mapillary Image").triangulate().material(material)
        plane = ddd.uv.map_cubic(plane)
        plane = plane.recenter()
        plane = plane.rotate(ddd.ROT_FLOOR_TO_FRONT)

        return plane

    def request_image(self, key, size='1024'):
        """
        URL: https://images.mapillary.com/{key}/thumb-1024.jpg
        """
        filename = "_cache/images/mapillary/%s-%s.jpg" % (key, size)
        if os.path.exists(filename): return

        url = self.url_images + key + ('/thumb-%s.jpg' % size)
        print("Requesting: %s" % url)
        r = requests.get(url)
        data = r.content

        with open(filename, "wb") as f:
            f.write(data)


if __name__ == '__main__':

    mc = MapillaryClient()
    data = mc.images_list([-3.693955, 40.400690])





