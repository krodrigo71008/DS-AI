from __future__ import annotations
from typing import TYPE_CHECKING

from modeling.objects.ObjectWithMultipleForms import ObjectWithMultipleForms
from utility.GameTime import GameTime
if TYPE_CHECKING:
    from modeling.Scheduler import Scheduler
    from utility.Point2d import Point2d

REEDS_READY = 98
REEDS_HARVESTED = 186


class Reeds(ObjectWithMultipleForms):
    def __init__(self, position : Point2d, latest_screen_position : Point2d, id_ : int, scheduler : Scheduler):
        super().__init__(False, position, latest_screen_position, [REEDS_READY, REEDS_HARVESTED], id_, scheduler)
        if id_ == REEDS_HARVESTED:
            scheduler.schedule_change(GameTime(non_winter_days=3), position, "grow", self)

    def update(self, change : str):
        if change == "grow":
            self._state = REEDS_READY

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
        self._state = REEDS_HARVESTED
        self.scheduler.schedule_change(GameTime(non_winter_days=3), self.position, "grow", self)

    def is_harvested(self) -> bool:
        return self._state == REEDS_HARVESTED

    def set_state(self, state):
        if state not in self.object_ids:
            raise Exception("Invalid id!")
        self._state = state


