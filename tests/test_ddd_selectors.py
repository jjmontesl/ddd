
from ddd.ddd import ddd
from unittest import TestCase

# TODO: Tests for (future v2) selectors:

'''

# Are paths always considered from current node, or does 'Node1' match the name at any children level (as opossed to, e.g.: ./Node1 )
# do like XML? Overpass? (favour XML)

/Node1
/Node1/Node2
/*Node2
Node1
Node1/Node2
*/Node2

Node1/Node2/Node3
*/Node3                 # Fail
**/Node3

[a=1]
Node1[a=1]
Node1[a=1][b=2]

[a=1]/[b=2]
Node[a=1]/*[b=2]        # ?
Node[a=1]/**/[b=2]      # ?

/Node */                # Partial name matches (also support {}... or regex?)

Test selectors with attributes present in nested children at different levels, check/formalize recurse=yes/no vs **...
'''


'''
def setup... (check test API for setup, etc)
    """
    /Node1
    /Node2
        /Node3
    /Node1b {}
    /Node2
        /Node3
    """
    pass
'''

class SelectorTestCase(TestCase):

    def setUp(self):
        node = ddd.DDDNode2(name="TestNode")
        self.root = node

    def test_selector_simple(self):
        """
        Tests simple selectors.
        """
        result = self.root.select(selector='["ddd:name" = "TestNode"]')
        #print(result.children)
        self.assertGreater(len(result.children), 0)

