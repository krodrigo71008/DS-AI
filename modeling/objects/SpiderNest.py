from __future__ import annotations
from typing import TYPE_CHECKING

from modeling.objects.ObjectWithMultipleForms import ObjectWithMultipleForms
from utility.GameTime import GameTime
if TYPE_CHECKING:
    from modeling.Scheduler import Scheduler
    from utility.Point2d import Point2d

NEST_SMALL = 34
NEST_MEDIUM = 74
NEST_BIG = 75

class SpiderNest(ObjectWithMultipleForms):
    def __init__(self, position : Point2d, latest_screen_position : Point2d, id_ : int, scheduler : Scheduler):
        super().__init__(False, position, latest_screen_position, [NEST_SMALL, NEST_MEDIUM, NEST_BIG], id_, scheduler)
        # times are random, 5-10 days, 5-10 days, 12.5-25 days, but I'm using the maximum value
        if id_ == NEST_SMALL:
            scheduler.schedule_change(GameTime(days=10), position, "growToMedium", self)
        elif id_ == NEST_MEDIUM:
            scheduler.schedule_change(GameTime(days=10), position, "growToBig", self)
        else: # NEST_BIG
            scheduler.schedule_change(GameTime(days=25), position, "growToSmall", self)

    def update(self, change : str):
        if change == "growToSmall":
            self._state = NEST_SMALL
            self.scheduler.schedule_change(GameTime(days=10), self.position, "growToMedium", self)
        elif change == "growToMedium":
            self._state = NEST_MEDIUM
            self.scheduler.schedule_change(GameTime(days=10), self.position, "growToBig", self)
        elif change == "growToBig":
            self._state = NEST_BIG
            self.scheduler.schedule_change(GameTime(days=25), self.position, "growToSmall", self)

    def handle_object_detected(self, state):
        if state not in self.object_ids:
            raise Exception("Invalid id!")
        if state == self._state:
            return
        if state == NEST_SMALL:
            self.set_state(NEST_SMALL)
            # self.update_function("growToMedium", GameTime(minutes=2*5), self)
        elif state == NEST_MEDIUM:
            self.set_state(NEST_MEDIUM)
            # self.update_function("growToBig", GameTime(minutes=7*5), self)
        else: # NEST_BIG
            self.set_state(NEST_BIG)

    def set_state(self, state):
        if state not in self.object_ids:
            raise Exception("Invalid id!")
        self._state = state
        self._state = state

    def is_small(self):
        return self._state == NEST_SMALL

    def is_medium(self):
        return self._state == NEST_MEDIUM

    def is_big(self):
        return self._state == NEST_BIG


