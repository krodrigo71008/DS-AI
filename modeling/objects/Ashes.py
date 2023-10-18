from __future__ import annotations
from typing import TYPE_CHECKING

from modeling.objects.ObjectWithSingleForm import ObjectWithSingleForm
from utility.GameTime import GameTime
if TYPE_CHECKING:
    from modeling.Scheduler import Scheduler
    from utility.Point2d import Point2d

class Ashes(ObjectWithSingleForm):
    def __init__(self, position : Point2d, latest_screen_position : Point2d, scheduler : Scheduler):
        super().__init__(True, position, latest_screen_position)
        self.scheduler = scheduler
        scheduler.schedule_change(GameTime(seconds=20), position, "disappear", self)

    def update(self, change : str):
        pass
