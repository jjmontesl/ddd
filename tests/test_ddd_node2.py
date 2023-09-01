from unittest import TestCase
from ddd.ddd import ddd


class DDDNode2TestCase(TestCase):

    def test_vertex_count_empty(self):
        node = ddd.DDDNode2()
        self.assertEqual(node.vertex_count(), 0)

    def test_vertex_count_line(self):
        node = ddd.line([[0, 0], [1, 1]])
        self.assertEqual(node.vertex_count(), 2)

    def test_vertex_count_polygon(self):
        
        node = ddd.disc(r=1)
        self.assertEqual(node.vertex_count(), 16 + 1)

        node = ddd.disc(r=1, resolution=1)
        self.assertEqual(node.vertex_count(), 4 + 1)

        node = ddd.disc(r=1, resolution=2)
        self.assertEqual(node.vertex_count(), 8 + 1)

    def test_vertex_count_multipolygon(self):
        node = ddd.rect([1, 1]).union(ddd.rect([1, 1]).translate([2, 2]))
        self.assertEqual(node.vertex_count(), (4 + 1) * 2)

    def test_vertex_count_geometrycollection(self):
        node = ddd.rect([1, 1]).union(ddd.line([[0, 0], [1, 1]]).translate([2, 2]))
        self.assertEqual(node.vertex_count(), (4 + 1) + 2)

        