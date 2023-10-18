from __future__ import annotations
from typing import TYPE_CHECKING

from modeling.objects.ObjectWithMultipleForms import ObjectWithMultipleForms
from utility.GameTime import GameTime
if TYPE_CHECKING:
    from modeling.Scheduler import Scheduler
    from utility.Point2d import Point2d

EVERGREEN_SMALL = 31
EVERGREEN_MEDIUM = 32
EVERGREEN_BIG = 33
EVERGREEN_DEAD = 57


class Evergreen(ObjectWithMultipleForms):
    def __init__(self, position : Point2d, latest_screen_position : Point2d, id_ : int, scheduler : Scheduler):
        super().__init__(False, position, latest_screen_position,
                         [EVERGREEN_SMALL, EVERGREEN_MEDIUM, EVERGREEN_BIG, EVERGREEN_DEAD], id_, scheduler)
        # times are random, 1*5-2*5, 3*5-7*5, 3*5-7*5 and 0.5*5-1.5*5, but I'm using the maximum value
        if id_ == EVERGREEN_SMALL:
            scheduler.schedule_change(GameTime(minutes=2*5), position, "growToMedium", self)
        elif id_ == EVERGREEN_MEDIUM:
            scheduler.schedule_change(GameTime(minutes=7*5), position, "growToBig", self)
        elif id_ == EVERGREEN_BIG:
            scheduler.schedule_change(GameTime(minutes=7*5), position, "growToDead", self)
        else:
            scheduler.schedule_change(GameTime(minutes=1.5*5), position, "growToSmall", self)

    def update(self, change : str):
        if change == "growToSmall":
            self._state = EVERGREEN_SMALL
            self.scheduler.schedule_change(GameTime(minutes=2*5), self.position, "growToMedium", self)
        if change == "growToMedium":
            self._state = EVERGREEN_MEDIUM
            self.scheduler.schedule_change(GameTime(minutes=7*5), self.position, "growToBig", self)
        if change == "growToBig":
            self._state = EVERGREEN_BIG
            self.scheduler.schedule_change(GameTime(minutes=7*5), self.position, "growToDead", self)
        if change == "growToDead":
            self._state = EVERGREEN_DEAD
            self.scheduler.schedule_change(GameTime(minutes=1.5*5), self.position, "growToSmall", self)

    def handle_object_detected(self, state):
        if state not in self.object_ids:
            raise Exception("Invalid id!")
        if state == self._state:
            return
        if state == EVERGREEN_SMALL:
            self.set_state(EVERGREEN_SMALL)
            # self.update_function("growToMedium", GameTime(minutes=2*5), self)
        elif state == EVERGREEN_MEDIUM:
            self.set_state(EVERGREEN_MEDIUM)
            # self.update_function("growToBig", GameTime(minutes=7*5), self)
        elif state == EVERGREEN_BIG:
            self.set_state(EVERGREEN_BIG)
            # self.update_function("growToDead", GameTime(minutes=7*5), self)
        else:
            self.set_state(EVERGREEN_DEAD)
            # self.update_function("growToSmall", GameTime(minutes=1.5*5), self)

    def set_state(self, state):
        if state not in self.object_ids:
            raise Exception("Invalid id!")
        self._state = state


