from modeling.constants import CYCLES_FOR_MOB_REMOVAL
from utility.Point2d import Point2d


class MobModel:
    def __init__(self, position : Point2d, id_ : int, name : str, latest_screen_position: Point2d):
        self.position = position
        self.id = id_
        self.name = name
        self.latest_screen_position = latest_screen_position
        self._cycles_to_be_deleted = CYCLES_FOR_MOB_REMOVAL

    def set_position(self, x : float, z : float):
        self.position = Point2d(x, z)

    def update(self, change):
        pass

    def handle_mob_detected(self, image_id):
        pass

    def name_str(self) -> str:
        return self.name

    def reset_cycles_to_be_deleted(self) -> None:
        self._cycles_to_be_deleted = CYCLES_FOR_MOB_REMOVAL
    
    def countdown_cycles_to_be_deleted(self) -> None:
        self._cycles_to_be_deleted -= 1

    def get_cycles_to_be_deleted(self) -> int:
        return self._cycles_to_be_deleted
