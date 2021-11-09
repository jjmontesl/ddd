class Cube:
    """A bounding box / bounding cube!"""
    __slots__ = ['x0', 'y0', 'x1', 'y1', 'z0', 'z1']

    # bounding box
    def __init__(self, x0=0, y0=0, z0=0, x1=0, y1=0, z1=0):
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.z0 = z0
        self.z1 = z1

    @property
    def width(self):
        return (self.x1 - self.x0)

    @property
    def height(self):
        return (self.y1 - self.y0)

    @property
    def depth(self):
        return (self.z1 - self.z0)


class TernaryTree(Cube):
    """
    Ternary tree node where each node also has a bounding box interface.

    If the node has no children, its bounding box represents empty space.

    Otherwise, its bounding box is split below and to the right and
    outwards by exactly three children, for which the same definition applies
    recursively.
    """

    __slots__ = ['right', 'down', 'out']

    def __init__(self, bound):
        super().__init__(bound.x0, bound.y0, bound.z0, bound.x1, bound.y1, bound.z1)
        self.right = None
        self.down  = None
        self.out   = None

    def isEmpty(self):
        return (self.right is None) and (self.down is None) and (self.out is None)

    def fit(self, item):
        """
        If empty: fit an item into this node, splitting it into three empty
        child nodes.

        If full: recursively try to fit it into its child nodes.

        The `item` argument is anything with a width and a height. Depth is
        assumed to be always 1.
        """
        # Returns False or the bbox that the item can fit into
        # item is anything with a width and height property

        if not self.isEmpty():
            # recurse down to a leaf with empty space and attempt to fit
            fit_right = self.right.fit(item)
            if fit_right: return fit_right

            fit_down = self.down.fit(item)
            if fit_down: return fit_down

            fit_out = self.out.fit(item)
            if fit_out: return fit_out

            # no room in any leaf
            return False

        # this node is empty, so attempt to fit the given bounding box
        w = item.width
        h = item.height
        d = item.depth
        assert d == 1 # don't need the general case

        # Doesn't fit
        if (w > self.width):    return False
        if (h > self.height):   return False
        if self.depth < d:      return False

        # it fits, so split the remaining space into two bounding boxes
        # given that the list of inputs to fit is sorted on descending height,
        # we can maximise height by splitting on the bottom edge first

        bbox = Cube
        right  = bbox(self.x0 + w, self.y0,     self.z0, self.x1,     self.y0 + h, self.z0 + d)
        down   = bbox(self.x0,     self.y0 + h, self.z0, self.x1,     self.y1,     self.z0 + d)
        out    = bbox(self.x0,     self.x0,     self.z0 + d, self.x1,     self.y1, self.z1)
        fitbox = bbox(self.x0,     self.y0,     self.z0, self.x0 + w, self.y0 + h, self.z0 + d)

        self.right = TernaryTree(right)
        self.down  = TernaryTree(down)
        self.out   = TernaryTree(out)

        return fitbox
