from __future__ import annotations
from typing import TYPE_CHECKING

from modeling.objects.ObjectWithSingleForm import ObjectWithSingleForm
if TYPE_CHECKING:
    from modeling.Modeling import Modeling
    from modeling.SlamIndexManager import SlamIndexManager
    from utility.Point2d import Point2d


class TallbirdNest(ObjectWithSingleForm):
    def __init__(self, modeling : Modeling, slam_state_index : int, latest_screen_position :  Point2d, image_id : int, 
                 slam_index_manager : SlamIndexManager):
        super().__init__(modeling, slam_state_index, False, latest_screen_position, image_id, slam_index_manager)
        self.has_egg = False

    def update(self, change : str):
        pass

    def set_has_egg(self, has_egg):
        self.has_egg = has_egg
