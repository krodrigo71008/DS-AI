from modeling.InventoryObject import InventoryObject
from modeling.ObjectsInfo import objects_info
from utility.GameTime import GameTime


class InventorySlot:
    def __init__(self, position):
        # position is the inventory slot, so 0-14, "Head", "Body" or "Hand"
        self.position = position
        self.object : InventoryObject = None
        self.count : int = 0

    def is_full(self):
        if self.object is None:
            return False
        return self.count == self.object.stack_size

    def reset(self):
        self.object = None
        self.count = 0

    def add_item(self, id_, count):
        if self.object is not None:
            if self.object.id != id_:
                raise Exception("Wrong function usage, object being added conflicts with already existing one.")
            old_count = self.count
            self.count += count
            if self.count > self.object.stack_size:
                self.count = self.object.stack_size
            # For now, I'm always assuming that the new object has 100% spoilage
            if self.object.spoilage is not None:
                self.object.spoilage = GameTime(seconds=(self.object.spoilage.seconds() * old_count
                                        + objects_info.get_item_info(info="spoil_time", image_id=self.object.id).seconds()
                                        * (self.count - old_count)) / self.count)
        else:
            self.object = InventoryObject(id_)
            self.count = count
            if self.count > self.object.stack_size:
                self.count = self.object.stack_size

    def change_item(self, id_, count):
        self.reset()
        if id_ is not None:
            self.add_item(id_, count)

    def get_slot_info(self) -> tuple[InventoryObject, int]:
        return self.object, self.count

    def trade_slot(self, other_slot):
        obj_help = self.object
        count_help = self.count
        other_obj, other_count = other_slot.get_slot_info()
        if other_obj is not None:
            self.change_item(other_obj.id, other_count)
        else:
            self.change_item(None, other_count)
        if obj_help is not None:
            other_slot.change_item(obj_help.id, count_help)
        else:
            other_slot.change_item(None, count_help)

    def no_durability(self):
        # note to remember that things like lantern don't break with 0 durability, but for now this is fine
        self.object = None
