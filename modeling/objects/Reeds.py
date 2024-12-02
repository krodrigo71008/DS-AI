from __future__ import annotations
from typing import TYPE_CHECKING

from modeling.objects.ObjectWithMultipleForms import ObjectWithMultipleForms
from utility.GameTime import GameTime
if TYPE_CHECKING:
    from modeling.Modeling import Modeling
    from modeling.Scheduler import Scheduler
    from modeling.SlamIndexManager import SlamIndexManager
    from utility.Point2d import Point2d

REEDS_READY = 98
REEDS_HARVESTED = 186


class Reeds(ObjectWithMultipleForms):
    def __init__(self, modeling : Modeling, slam_state_index : int, latest_screen_position : Point2d, image_id : int, scheduler : Scheduler,
                 slam_index_manager : SlamIndexManager):
        super().__init__(modeling, slam_state_index, False, latest_screen_position, [REEDS_READY, REEDS_HARVESTED], image_id, scheduler,
                         slam_index_manager)
        if image_id == REEDS_HARVESTED:
            scheduler.schedule_change(GameTime(non_winter_days=3), "grow", self)
            self.yield_ = None
        else:
            self.yield_ = "CutReeds"

    def update(self, change : str):
        if change == "grow":
            self.set_state(REEDS_READY)

    def handle_object_detected(self, state) -> None:
        if state not in self.object_ids:
            raise Exception("Invalid id!")
        if state == self._state:
            return
        if state == REEDS_READY:
            self.set_state(REEDS_READY)
        else:
            self.set_state(REEDS_HARVESTED)

    def harvest(self):
        self.set_state(REEDS_HARVESTED)
        self.scheduler.schedule_change(GameTime(non_winter_days=3), "grow", self)

    def is_harvested(self) -> bool:
        return self._state == REEDS_HARVESTED

    def set_state(self, state):
        if state not in self.object_ids:
            raise Exception("Invalid id!")
        self._state = state
        if state == REEDS_HARVESTED:
            self.yield_ = None
        else:
            self.yield_ = "CutReeds"


