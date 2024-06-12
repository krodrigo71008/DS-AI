from __future__ import annotations
from typing import TYPE_CHECKING

from modeling.objects.ObjectWithMultipleForms import ObjectWithMultipleForms
from utility.GameTime import GameTime
if TYPE_CHECKING:
    from modeling.Modeling import Modeling
    from modeling.Scheduler import Scheduler
    from modeling.SlamIndexManager import SlamIndexManager
    from utility.Point2d import Point2d

BERRYBUSH_READY = 35
BERRYBUSH_HARVESTED = 36


class BerryBush(ObjectWithMultipleForms):
    def __init__(self, modeling : Modeling, slam_state_index : int, latest_screen_position : Point2d, image_id : int, scheduler : Scheduler,
                 slam_index_manager : SlamIndexManager):
        super().__init__(modeling, slam_state_index, False, latest_screen_position, [BERRYBUSH_READY, BERRYBUSH_HARVESTED], image_id, scheduler,
                         slam_index_manager)
        if image_id == BERRYBUSH_HARVESTED:
            scheduler.schedule_change(GameTime(non_winter_days=4.6875), "grow", self)

    def update(self, change : str):
        if change == "grow":
            self._state = BERRYBUSH_READY

    def handle_object_detected(self, state):
        if state not in self.object_ids:
            raise Exception("Invalid id!")
        if state == self._state:
            return
        if state == BERRYBUSH_READY:
            self.set_state(BERRYBUSH_READY)
        else:
            self.set_state(BERRYBUSH_HARVESTED)

    def harvest(self):
        self._state = BERRYBUSH_HARVESTED
        self.scheduler.schedule_change(GameTime(non_winter_days=4.6875), "grow", self)

    def is_harvested(self) -> bool:
        return self._state == BERRYBUSH_HARVESTED

    def set_state(self, state):
        if state not in self.object_ids:
            raise Exception("Invalid id!")
        self._state = state


