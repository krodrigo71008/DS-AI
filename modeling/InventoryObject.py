from modeling.ObjectsInfo import objects_info
from utility.GameTime import GameTime


class InventoryObject:
    def __init__(self, id_ : int):
        # id is object id
        self.id = id_
        self.update_info()

    def rot(self) -> None:
        """Make the item rot
        """
        if self.spoilage is None:
            raise Exception("Object that doesn't spoil can't rot")
        self.id = objects_info.get_item_info(info="obj_id", name="Rot")
        self.update_info()

    def update_info(self) -> None:
        self.name = objects_info.get_item_info(info="name", obj_id=self.id)
        self.stack_size = objects_info.get_item_info(info="stack_size", obj_id=self.id)
        # spoilage
        self.spoilage : GameTime = objects_info.get_item_info(info="spoil_time", obj_id=self.id)
        self.uses_left = objects_info.get_item_info(info="max_uses", obj_id=self.id)
        self.time_left = objects_info.get_item_info(info="use_time", obj_id=self.id)
