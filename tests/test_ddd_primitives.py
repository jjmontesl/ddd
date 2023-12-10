from unittest import TestCase
from ddd.ddd import ddd


class DDDPrimitivesTestCase(TestCase):

    def test_ddd_point(self):
        
        node = ddd.point()
        self.assertEqual(node.geom.type, 'Point')
        self.assertEqual(node.vertex_count(), 1)
        self.assertEqual(node.geom.coords[0], (0.0, 0.0, 0.0))  # Points are defined to always be created with Z coordinate

        node = ddd.point([0, 0, 0])
        self.assertEqual(node.geom.type, 'Point')
        self.assertEqual(node.vertex_count(), 1)
        self.assertEqual(node.geom.coords[0], (0.0, 0.0, 0.0))

        node = ddd.point(name="TestPoint")
        self.assertEqual(node.geom.type, 'Point')
        self.assertEqual(node.vertex_count(), 1)
        self.assertEqual(node.geom.coords[0], (0.0, 0.0, 0.0))
        self.assertEqual(node.name, "TestPoint")

        node = ddd.point([1, 1])
        self.assertEqual(node.geom.type, 'Point')
        self.assertEqual(node.vertex_count(), 1)
        self.assertEqual(node.geom.coords[0], (1.0, 1.0, 0.0))

        self.assertEqual(node.length(), 0.0)
        self.assertEqual(node.area(), 0.0)


    def test_ddd_line(self):

        node = ddd.line([(0, 0), (1, 1)])
        self.assertEqual(node.geom.type, 'LineString')
        self.assertEqual(node.vertex_count(), 2)
        self.assertEqual(node.geom.coords[0], (0.0, 0.0))
        self.assertEqual(node.geom.coords[1], (1.0, 1.0))
        
        self.assertEqual(node.length(), ddd.SQRT_2)
        self.assertEqual(node.area(), 0.0)

        node = ddd.line([(0, 0, 0), (1, 1, 0)])
        self.assertEqual(node.geom.type, 'LineString')
        self.assertEqual(node.vertex_count(), 2)
        self.assertEqual(node.geom.coords[0], (0.0, 0.0, 0.0))
        self.assertEqual(node.geom.coords[1], (1.0, 1.0, 0.0))

    def test_ddd_rect(self):

        node = ddd.rect((1, 1))
        self.assertEqual(node.geom.type, 'Polygon')
        self.assertEqual(node.vertex_count(), 4 + 1)
        self.assertEqual(node.geom.bounds, (0.0, 0.0, 1.0, 1.0))
        self.assertEqual(node.vertex_list()[0], (0.0, 0.0, 0.0))
        self.assertEqual(node.vertex_list()[1], (1.0, 0.0, 0.0))
        self.assertEqual(node.vertex_list()[2], (1.0, 1.0, 0.0))
        self.assertEqual(node.vertex_list()[3], (0.0, 1.0, 0.0))
        #self.assertEqual(len(node.vertex_list()), 4)  # 4 or 4 + 1?
        
        self.assertEqual(node.length(), 4.0)
        self.assertEqual(node.area(), 1.0)

        node = ddd.rect([(0, 0, 0), (1, 1, 0)], name="TestRect")
        self.assertEqual(node.geom.type, 'Polygon')
        self.assertEqual(node.vertex_count(), 4 + 1)
        self.assertEqual(node.geom.bounds, (0.0, 0.0, 1.0, 1.0))
        self.assertEqual(node.vertex_list()[0], (0.0, 0.0, 0.0))
        self.assertEqual(node.vertex_list()[1], (1.0, 0.0, 0.0))
        self.assertEqual(node.vertex_list()[2], (1.0, 1.0, 0.0))
        self.assertEqual(node.vertex_list()[3], (0.0, 1.0, 0.0))
        self.assertEqual(node.name, "TestRect")


    '''
    def polygon(self, coords, name=None):
    def regularpolygon(self, sides, r=1.0, name=None):
    def shape(self, geometry, name=None):
    def svgpath(self, path, name=None):
    def geometry(self, geometry):
    def rect(self,  bounds=None, name=None):
    def disc(self, center=None, r=None, resolution=4, name=None) -> DDDNode2:
    '''
