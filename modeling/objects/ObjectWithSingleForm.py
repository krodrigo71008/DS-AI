from __future__ import annotations
from typing import TYPE_CHECKING

from modeling.objects.ObjectModel import ObjectModel
if TYPE_CHECKING:
    from modeling.Scheduler import Scheduler
    from utility.Point2d import Point2d


class ObjectWithSingleForm(ObjectModel):
    # object_ids should be an array like this: [id1, id2]
    def __init__(self, pickable : bool, position : Point2d, latest_screen_position : Point2d):
        super().__init__(pickable, position, latest_screen_position)
    
    def name_str(self) -> str:
        return type(self).__name__
