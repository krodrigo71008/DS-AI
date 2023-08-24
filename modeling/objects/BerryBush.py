import heapq
import time

from modeling.objects.ObjectWithMultipleForms import ObjectWithMultipleForms
from utility.GameTime import GameTime
from utility.Point2d import Point2d
from utility.Clock import Clock

BERRYBUSH_READY = 35
BERRYBUSH_HARVESTED = 36


class BerryBush(ObjectWithMultipleForms):
    def __init__(self, position : Point2d, latest_screen_position : Point2d, id_ : int, update_queue : list[float, int, int, str], clock: Clock):
        super().__init__(False, position, latest_screen_position, [BERRYBUSH_READY, BERRYBUSH_HARVESTED], id_, update_queue, clock)
        if id_ == BERRYBUSH_HARVESTED:
            heapq.heappush(update_queue, (clock.time_from_now(GameTime(non_winter_days=4.6875)), time.time(), position, "grow", self))

    def update(self, change):
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
        heapq.heappush(self.update_queue, (self.clock.time_from_now(GameTime(non_winter_days=4.6875)), time.time(), self.position, "grow", self))

    def is_harvested(self) -> bool:
        return self._state == BERRYBUSH_HARVESTED

    def set_state(self, state):
        if state not in self.object_ids:
            raise Exception("Invalid id!")
        self._state = state


