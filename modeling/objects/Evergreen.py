from __future__ import annotations
from typing import TYPE_CHECKING

from modeling.objects.ObjectWithMultipleForms import ObjectWithMultipleForms
from utility.GameTime import GameTime
if TYPE_CHECKING:
    from modeling.Modeling import Modeling
    from modeling.Scheduler import Scheduler
    from modeling.SlamIndexManager import SlamIndexManager
    from utility.Point2d import Point2d

EVERGREEN_SMALL = 31
EVERGREEN_MEDIUM = 32
EVERGREEN_BIG = 33
EVERGREEN_DEAD = 57


class Evergreen(ObjectWithMultipleForms):
    def __init__(self, modeling : Modeling, slam_state_index : int, latest_screen_position : Point2d, image_id : int, scheduler : Scheduler, 
                 slam_index_manager : SlamIndexManager, lumpy : bool):
        super().__init__(modeling, slam_state_index, False, latest_screen_position,
                         [EVERGREEN_SMALL, EVERGREEN_MEDIUM, EVERGREEN_BIG, EVERGREEN_DEAD], image_id, scheduler, slam_index_manager)
        # times are random, 1*5-2*5, 3*5-7*5, 3*5-7*5 and 0.5*5-1.5*5, but I'm using the maximum value
        if image_id == EVERGREEN_SMALL:
            scheduler.schedule_change(GameTime(minutes=2*5), "growToMedium", self)
        elif image_id == EVERGREEN_MEDIUM:
            scheduler.schedule_change(GameTime(minutes=7*5), "growToBig", self)
        elif image_id == EVERGREEN_BIG:
            scheduler.schedule_change(GameTime(minutes=7*5), "growToDead", self)
        else:
            scheduler.schedule_change(GameTime(minutes=1.5*5), "growToSmall", self)
        self.lumpy = lumpy

    def update(self, change : str):
        if change == "growToSmall":
            self._state = EVERGREEN_SMALL
            self.scheduler.schedule_change(GameTime(minutes=2*5), "growToMedium", self)
        elif change == "growToMedium":
            self._state = EVERGREEN_MEDIUM
            self.scheduler.schedule_change(GameTime(minutes=7*5), "growToBig", self)
        elif change == "growToBig":
            self._state = EVERGREEN_BIG
            self.scheduler.schedule_change(GameTime(minutes=7*5), "growToDead", self)
        elif change == "growToDead":
            self._state = EVERGREEN_DEAD
            self.scheduler.schedule_change(GameTime(minutes=1.5*5), "growToSmall", self)

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

    def is_small(self):
        return self._state == EVERGREEN_SMALL

    def is_medium(self):
        return self._state == EVERGREEN_MEDIUM

    def is_big(self):
        return self._state == EVERGREEN_BIG

    def is_dead(self):
        return self._state == EVERGREEN_DEAD

