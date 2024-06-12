from __future__ import annotations
from typing import TYPE_CHECKING

from modeling.objects.ObjectModel import ObjectModel
if TYPE_CHECKING:
    from modeling.Modeling import Modeling
    from modeling.SlamIndexManager import SlamIndexManager
    from utility.Point2d import Point2d


class ObjectWithSingleForm(ObjectModel):
    def __init__(self, modeling : Modeling, slam_state_index : int, pickable : bool, latest_screen_position : Point2d, image_id : int,
                 slam_index_manager : SlamIndexManager):
        super().__init__(modeling, slam_state_index, pickable, latest_screen_position, image_id, slam_index_manager)
    
    def name_str(self) -> str:
        return type(self).__name__
