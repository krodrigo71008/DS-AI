from __future__ import annotations
from typing import TYPE_CHECKING

import math

from modeling.constants import CYCLES_FOR_OBJECT_REMOVAL
from utility.Point2d import Point2d
if TYPE_CHECKING:
    from modeling.Modeling import Modeling
    from modeling.SlamIndexManager import SlamIndexManager


class ObjectModel:
    def __init__(self, modeling : Modeling, slam_state_index : int, pickable : bool, latest_screen_position : Point2d, image_id : int,
                 slam_index_manager: SlamIndexManager):
        self.modeling = modeling
        self.slam_index_manager = slam_index_manager
        self.slam_index_manager.register(self, slam_state_index)
        self.pickable = pickable
        self.latest_screen_position = latest_screen_position
        self.image_id = image_id
        self._cycles_to_be_deleted = CYCLES_FOR_OBJECT_REMOVAL

    def reset_cycles_to_be_deleted(self) -> None:
        self._cycles_to_be_deleted = CYCLES_FOR_OBJECT_REMOVAL
    
    def countdown_cycles_to_be_deleted(self) -> None:
        self._cycles_to_be_deleted -= 1

    def get_cycles_to_be_deleted(self) -> int:
        return self._cycles_to_be_deleted
    
    def position(self) -> Point2d:
        slam_state_index = self.slam_index_manager.get_index(self)
        pos = self.modeling.xEst[slam_state_index:slam_state_index+2, 0]
        return Point2d(pos[0], pos[1])
    
    def std(self) -> tuple[float, float]:
        slam_state_index = self.slam_index_manager.get_index(self)
        cov_x1 = self.modeling.PEst[slam_state_index, slam_state_index]
        cov_x2 = self.modeling.PEst[slam_state_index+1, slam_state_index+1]
        return math.sqrt(cov_x1), math.sqrt(cov_x2)

    def slam_state_index(self) -> int:
        return self.slam_index_manager.get_index(self)

    def __str__(self) -> str:
        return f"{type(self).__name__} at {self.position()}"

    def name_str(self) -> str:
        raise NotImplementedError()

    def update(self, change : str):
        raise NotImplementedError()
