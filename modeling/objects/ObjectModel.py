from modeling.constants import CYCLES_FOR_OBJECT_REMOVAL
from utility.Point2d import Point2d


class ObjectModel:
    def __init__(self, pickable : bool, position : Point2d, latest_screen_position : Point2d):
        self.pickable = pickable
        self.position = position
        self.latest_screen_position = latest_screen_position
        self._cycles_to_be_deleted = CYCLES_FOR_OBJECT_REMOVAL

    def reset_cycles_to_be_deleted(self) -> None:
        self._cycles_to_be_deleted = CYCLES_FOR_OBJECT_REMOVAL
    
    def countdown_cycles_to_be_deleted(self) -> None:
        self._cycles_to_be_deleted -= 1

    def get_cycles_to_be_deleted(self) -> int:
        return self._cycles_to_be_deleted

    def __str__(self) -> str:
        return f"{type(self).__name__} at {self.position}"

    def name_str(self) -> str:
        raise NotImplementedError()

    def set_position(self, x : float, z : float):
        self.position = Point2d(x, z)

    def update(self, change : str):
        raise NotImplementedError()
