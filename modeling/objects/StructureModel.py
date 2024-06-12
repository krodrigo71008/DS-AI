from __future__ import annotations
from typing import TYPE_CHECKING

from modeling.objects.ObjectWithSingleForm import ObjectWithSingleForm
if TYPE_CHECKING:
    from modeling.Modeling import Modeling
    from modeling.SlamIndexManager import SlamIndexManager
    from utility.Point2d import Point2d


class StructureModel(ObjectWithSingleForm):
    def __init__(self, modeling : Modeling, slam_state_index : int, latest_screen_position : Point2d, id_ : int, image_id : int, name : str,
                 slam_index_manager : SlamIndexManager):
        super().__init__(modeling, slam_state_index, False, latest_screen_position, image_id, slam_index_manager)
        self.id = id_
        self.name = name

    def update(self, change : str):
        pass

    def name_str(self) -> str:
        return self.name
