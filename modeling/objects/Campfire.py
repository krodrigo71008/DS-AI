from __future__ import annotations
from typing import TYPE_CHECKING

from modeling.objects.ObjectWithMultipleForms import ObjectWithMultipleForms
if TYPE_CHECKING:
    from modeling.Scheduler import Scheduler
    from utility.Point2d import Point2d


class Campfire(ObjectWithMultipleForms):
    def __init__(self, position : Point2d, latest_screen_position : Point2d, id_ : int, scheduler : Scheduler):
        super().__init__(False, position, latest_screen_position, [45], id_, scheduler)
        # I'll add the other states later

    def update(self, change : str):
        pass

    def handle_object_detected(self, state):
        pass

    def set_state(self, state):
        if state not in self.object_ids:
            raise Exception("Invalid id!")
        self._state = state


