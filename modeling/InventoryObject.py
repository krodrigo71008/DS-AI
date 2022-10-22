from modeling.ObjectsInfo import objects_info
from utility.GameTime import GameTime


class InventoryObject:
    def __init__(self, id_):
        # id is object id
        self.id = id_
        self.name = objects_info.get_item_info(info="name", obj_id=id_)
        self.stack_size = objects_info.get_item_info(info="stack_size", obj_id=id_)
        # spoilage
        self.spoilage : GameTime = objects_info.get_item_info(info="spoil_time", obj_id=id_)
        self.uses_left = objects_info.get_item_info(info="max_uses", obj_id=id_)
        self.time_left = objects_info.get_item_info(info="use_time", obj_id=id_)

    def rot(self):
        if self.spoilage is None:
            raise Exception("Object that doesn't spoil can't rot")
        self.id = objects_info.get_item_info(info="obj_id", name="Rot")
        self.spoilage = GameTime(days=None)

