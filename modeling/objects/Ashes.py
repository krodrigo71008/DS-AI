import heapq
import time

from modeling.objects.ObjectModel import ObjectModel
from utility.GameTime import GameTime
from utility.Point2d import Point2d
from utility.Clock import Clock

class Ashes(ObjectModel):
    def __init__(self, position : Point2d, latest_screen_position : Point2d, update_queue : list[float, int, int, str], clock: Clock):
        super().__init__(True, position, latest_screen_position)

        heapq.heappush(update_queue, (clock.time_from_now(GameTime(seconds=20)), time.time(), self.position, "disappear", self))

    def update(self, change):
        pass
