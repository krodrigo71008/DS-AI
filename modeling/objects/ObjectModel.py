from utility.Point2d import Point2d


class ObjectModel:
    def __init__(self, pickable, position):
        self.pickable = pickable
        self.position = position

    def set_position(self, x, z):
        self.position = Point2d(x, z)

    def update(self, change):
        raise NotImplementedError()
