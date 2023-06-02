
from ddd.ddd import ddd


def test_selector_simple():
    """
    Tests simple selectors.
    """
    node = ddd.DDDNode2(name="TestNode")
    result = node.select(selector='["ddd:name" = "TestNode"]')
    #print(result.children)
    assert(result.children)

