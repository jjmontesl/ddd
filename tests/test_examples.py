from unittest import TestCase

from ddd.ddd import ddd
from ddd.core import settings
from ddd.core.cli import D1D2D3Bootstrap
from ddd.pipeline.pipeline import DDDPipeline


class DDDExamplesTestCase(TestCase):

    def test_ddd_example_catenary(self):
        
        script = "examples/catenary.py"
        
        ddd_bootstrap = D1D2D3Bootstrap()
        ddd_bootstrap.parse_args(["run", script])
        D1D2D3Bootstrap.renderer = "none"

        pipeline = DDDPipeline(script)
        pipeline.run()
        #pipeline.root.dump()
        node = pipeline.root

        self.assertEqual(node.count(), 1)
        self.assertEqual(node.find("Catenary test").count(), 26)

