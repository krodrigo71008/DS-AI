from modeling.constants import CYCLES_FOR_OBJECT_REMOVAL
from utility.Point2d import Point2d


class ObjectModel:
    def __init__(self, pickable, position, latest_screen_position):
        self.pickable = pickable
        self.position = position
        self.latest_screen_position = latest_screen_position
        self.cycles_to_be_deleted = CYCLES_FOR_OBJECT_REMOVAL

    def __str__(self) -> str:
        return f"{type(self).__name__} at {self.position}"

    def set_position(self, x, z):
        self.position = Point2d(x, z)

    def update(self, change):
        raise NotImplementedError()
