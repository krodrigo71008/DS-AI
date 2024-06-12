from __future__ import annotations
from typing import TYPE_CHECKING

from modeling.objects.ObjectWithSingleForm import ObjectWithSingleForm
from utility.GameTime import GameTime
if TYPE_CHECKING:
    from modeling.Modeling import Modeling
    from modeling.Scheduler import Scheduler
    from modeling.SlamIndexManager import SlamIndexManager
    from utility.Point2d import Point2d

class Ashes(ObjectWithSingleForm):
    def __init__(self, modeling : Modeling, slam_state_index : int, latest_screen_position : Point2d, image_id : int, scheduler : Scheduler,
                 slam_index_manager: SlamIndexManager):
        super().__init__(modeling, slam_state_index, True, latest_screen_position, image_id, slam_index_manager)
        self.scheduler = scheduler
        scheduler.schedule_change(GameTime(seconds=20), "disappear", self)

    def update(self, change : str):
        pass
