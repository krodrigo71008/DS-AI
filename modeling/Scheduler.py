from __future__ import annotations
import time
import heapq
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from modeling.WorldModel import WorldModel
    from modeling.objects.ObjectModel import ObjectModel
    from utility.Clock import Clock
    from utility.GameTime import GameTime
    from utility.Point2d import Point2d

class Scheduler:
    def __init__(self, clock : Clock, world_model : WorldModel):
        # update_queue has (time, object_id, index, change, instance)
        self.update_queue = []
        self.clock = clock
        self.world_model = world_model
    
    def update(self) -> None:
        # the [0] gets the 'timestamp' in which the change should happen
        while len(self.update_queue) > 0 and self.update_queue[0][0] < self.clock.time():
            tup = heapq.heappop(self.update_queue)
            pos = tup[2]
            change = tup[3]
            instance = tup[4]
            if change == "disappear":
                self.world_model.remove_object(instance, pos)
            else:
                instance.update(change)
    
    def schedule_change(self, time_from_now : GameTime, position : Point2d, change : str, instance : ObjectModel):
        heapq.heappush(self.update_queue, (self.clock.time_from_now(time_from_now), time.time(), position, change, instance))

class SchedulerMock(Scheduler):
    def __init__(self, clock : Clock, world_model : WorldModel):
        super().__init__(clock, world_model)
        
    def update(self) -> None:
        pass
    
    def schedule_change(self, time_from_now : GameTime, position : Point2d, change : str, instance : ObjectModel):
        pass
