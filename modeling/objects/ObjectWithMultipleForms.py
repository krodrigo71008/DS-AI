from __future__ import annotations
from typing import TYPE_CHECKING

import pandas as pd

from modeling.objects.ObjectModel import ObjectModel
if TYPE_CHECKING:
    from modeling.Scheduler import Scheduler
    from utility.Point2d import Point2d


class ObjectWithMultipleForms(ObjectModel):
    # object_ids should be an array like this: [id1, id2]
    def __init__(self, pickable : bool, position : Point2d, latest_screen_position : Point2d, 
                 object_ids : list[int], initial_state : int, scheduler : Scheduler):
        if len(object_ids) == 0:
            raise Exception("Invalid empty list of object ids!")
        if type(object_ids) is not list:
            raise Exception("Invalid constructor arguments!")
        
        obj_info = pd.read_csv('utility/objects_info.csv')
        for obj_id in object_ids:
            assert obj_id in obj_info[obj_info["name"] == type(self).__name__]["image_id"]

        super().__init__(pickable, position, latest_screen_position)
        self.object_ids = object_ids
        self._state = initial_state
        self.scheduler = scheduler

    def handle_object_detected(self, state):
        raise NotImplementedError()

    def name_str(self) -> str:
        return f"{type(self).__name__}"
