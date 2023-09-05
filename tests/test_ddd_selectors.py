
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
        root = ddd.DDDNode2(name="TestNodeRoot")
        self.root = root
        
        nodedata = ddd.DDDNode2(name="TestNodeWithData")
        nodedata.set('test:bool:true', True)
        nodedata.set('test:bool:false', False)
        nodedata.set('test:bool:none', None)
        nodedata.set('test:bool:true:str1', "True")
        nodedata.set('test:bool:true:str2', "true")
        root.append(nodedata)    
        self.nodedata = nodedata


    def test_selector_simple(self):
        """
        Tests simple selectors.
        """
        result = self.root.select(selector='["ddd:name" = "TestNodeRoot"]')
        self.assertEqual(result.count(), 1)

    def test_selector_bool(self):
        """
        Tests boolean conditions.
        """
        result = self.root.select(selector='["test:bool:true" = true]')
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.one(), self.nodedata)

        result = self.root.select(selector='["test:bool:true" = True]')
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.one(), self.nodedata)

        result = self.root.select(selector='["test:bool:true" = false]')
        self.assertEqual(result.count(), 0)


        '''
        result = self.root.select(selector='["test:bool:true:str" = true]')
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.one(), self.nodedata)

        result = self.root.select(selector='["test:bool:true:str" = True]')
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.one(), self.nodedata)

        result = self.root.select(selector='["test:bool:true:str" = false]')
        self.assertEqual(result.count(), 0)
        '''


