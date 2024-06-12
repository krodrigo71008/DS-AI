from __future__ import annotations
from typing import TYPE_CHECKING

from modeling.objects.ObjectWithMultipleForms import ObjectWithMultipleForms
if TYPE_CHECKING:
    from modeling.Modeling import Modeling
    from modeling.Scheduler import Scheduler
    from modeling.SlamIndexManager import SlamIndexManager
    from utility.Point2d import Point2d


class Campfire(ObjectWithMultipleForms):
    def __init__(self, modeling : Modeling, slam_state_index : int, latest_screen_position : Point2d, image_id : int, scheduler : Scheduler,
                 slam_index_manager : SlamIndexManager):
        super().__init__(modeling, slam_state_index, False, latest_screen_position, [45], image_id, scheduler, slam_index_manager)
        # I'll add the other states later

    def update(self, change : str):
        pass

    def handle_object_detected(self, state):
        pass

    def set_state(self, state):
        if state not in self.object_ids:
            raise Exception("Invalid id!")
        self._state = state


