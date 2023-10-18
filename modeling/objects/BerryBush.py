from __future__ import annotations
from typing import TYPE_CHECKING

from modeling.objects.ObjectWithMultipleForms import ObjectWithMultipleForms
from utility.GameTime import GameTime
if TYPE_CHECKING:
    from modeling.Scheduler import Scheduler
    from utility.Point2d import Point2d

BERRYBUSH_READY = 35
BERRYBUSH_HARVESTED = 36


class BerryBush(ObjectWithMultipleForms):
    def __init__(self, position : Point2d, latest_screen_position : Point2d, id_ : int, scheduler : Scheduler):
        super().__init__(False, position, latest_screen_position, [BERRYBUSH_READY, BERRYBUSH_HARVESTED], id_, scheduler)
        if id_ == BERRYBUSH_HARVESTED:
            scheduler.schedule_change(GameTime(non_winter_days=4.6875), position, "grow", self)

    def update(self, change : str):
        if change == "grow":
            self._state = BERRYBUSH_READY

    def handle_object_detected(self, state):
        if state not in self.object_ids:
            raise Exception("Invalid id!")
        if state == self._state:
            return
        # update state and schedule growth if it was just picked
        if state == BERRYBUSH_READY:
            self.set_state(BERRYBUSH_READY)
        else:
            self.set_state(BERRYBUSH_HARVESTED)

    def harvest(self):
        self._state = BERRYBUSH_HARVESTED
        self.scheduler.schedule_change(GameTime(non_winter_days=4.6875), self.position, "grow", self)

    def is_harvested(self) -> bool:
        return self._state == BERRYBUSH_HARVESTED

    def set_state(self, state):
        if state not in self.object_ids:
            raise Exception("Invalid id!")
        self._state = state


