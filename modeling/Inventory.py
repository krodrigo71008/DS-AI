from modeling.InventorySlot import InventorySlot
from modeling.ObjectsInfo import objects_info
from utility.GameTime import GameTime


# change image ids to obj ids
class Inventory:
    def __init__(self):
        # keys 0-14 map to each slot
        self.slots = {
            0: InventorySlot(0),
            1: InventorySlot(1),
            2: InventorySlot(2),
            3: InventorySlot(3),
            4: InventorySlot(4),
            5: InventorySlot(5),
            6: InventorySlot(6),
            7: InventorySlot(7),
            8: InventorySlot(8),
            9: InventorySlot(9),
            10: InventorySlot(10),
            11: InventorySlot(11),
            12: InventorySlot(12),
            13: InventorySlot(13),
            14: InventorySlot(14),
            "Head": InventorySlot("Head"),
            "Body": InventorySlot("Body"),
            "Hand": InventorySlot("Hand"),
        }
        # the return_to attributes identify to where the currently equipped object should go when unequipped
        self.head_return_to : InventorySlot = None
        self.body_return_to : InventorySlot = None
        self.hand_return_to : InventorySlot = None
        self._list_of_changes = []

    def get_inventory_count(self, object_names: list[str]) -> list[int]:
        """
        Get how many of a certain item we have in our inventory
        :param object_names: list of object names in Pascal Case
        :type object_names: list[str]
        :return: count of the requested objects
        :rtype: list[int]
        """
        inv = {}
        for slot in self.slots.values():
            if slot.object is not None:
                if slot.object.name in inv:
                    inv[slot.object.name] += slot.count
                else:
                    inv[slot.object.name] = slot.count

        counts = []
        for object_name in object_names:
            if object_name in inv:
                counts.append(inv[object_name])
            else:
                counts.append(0)
        return counts

    def _find_first_empty_slot(self) -> int:
        """Find first empty inventory slot among the 15 non equipment slots

        :return: slot index or None if all slots are full
        :rtype: int
        """
        for i in range(15):
            if self.slots[i].object is None:
                return i
        return None

    def _find_first_non_full_slot(self, item_name : str) -> int:
        """Find first slot that has the requested item and is not full

        :param item_name: item name
        :type item_name: str
        :return: slot index or None if all slots don't fit
        :rtype: int
        """
        for i in range(15):
            if (self.slots[i].object is not None and
                    self.slots[i].object.id == objects_info.get_item_info(info="obj_id", name=item_name) and
                    not self.slots[i].is_full()):
                return i
        return None

    def find_first_slot(self, name : str) -> int:
        """Find first slot that has the requested item

        :param item_name: item name
        :type item_name: str
        :return: slot index or None if no slots have that item
        :rtype: int
        """
        for i in range(15):
            if (self.slots[i].object is not None and
                    self.slots[i].object.id == objects_info.get_item_info(info="obj_id", name=name)):
                return i
        return None

    def _get_slot(self, slot_name : str | int) -> InventorySlot:
        """Get slot according to the slot descriptor

        :param slot_name: 0-14, "Head", "Body" or "Hand"
        :type slot_name: str | int
        :return: requested inventory slot
        :rtype: InventorySlot
        """
        return self.slots[slot_name]

    def replace_inventory(self, slots_dict : dict[int | str, tuple[str, int]]) -> None:
        """Replace the specified inventory slots

        :param slots_dict: each key should be either a number from 0-14 or "Head", "Body", "Hand", value should be (name, count)
        :type slots_dict: dict[int | str, tuple[str, int]]
        """
        for slot_name, item_info in slots_dict.items():
            item_name, count = item_info
            obj_id = objects_info.get_item_info(info="obj_id", name=item_name)
            self.slots[slot_name].change_item(obj_id, count)

    def add_item(self, name : str, count : int) -> None:
        """Add item to inventory, as if picking it up

        :param name: item name
        :type name: str
        :param count: item count
        :type count: int
        """
        equip_slot = objects_info.get_item_info(info="equip_slot", name=name)
        if equip_slot is not None:
            if count != 1:
                raise ValueError("Incorrect usage, equippable items can't be stacked")
            if equip_slot == "Head":
                if self.slots["Head"].object is None:
                    self.slots["Head"].add_item(objects_info.get_item_info(info="obj_id", name=name), count)
                    return
            elif equip_slot == "Body":
                if self.slots["Body"].object is None:
                    self.slots["Body"].add_item(objects_info.get_item_info(info="obj_id", name=name), count)
                    return
            else:
                if self.slots["Hand"].object is None:
                    self.slots["Hand"].add_item(objects_info.get_item_info(info="obj_id", name=name), count)
                    return
        # checking if there is a non full slot with this item
        first_non_full_slot = self._find_first_non_full_slot(name)
        if first_non_full_slot is None:
            # no items of this type or only full stacks
            first_empty_slot = self._find_first_empty_slot()
            if first_empty_slot is None:
                raise Exception("Wrong usage! The inventory is full!")
            else:
                self.slots[first_empty_slot].add_item(
                    objects_info.get_item_info(info="obj_id", name=name), count)
                return
        else:
            # add item to existing stack and possibly fill new slot
            extra_count = self.slots[first_non_full_slot].count + count - objects_info.get_item_info(info="stack_size", name=name)
            self.slots[first_non_full_slot].add_item(
                objects_info.get_item_info(info="obj_id", name=name), count)
            if extra_count <= 0:
                return
            # add any items that didn't fit in the first stack to a new slot
            first_empty_slot = self._find_first_empty_slot()
            if first_empty_slot is None:
                raise Exception("Wrong usage! The inventory is full!")
            else:
                self.slots[first_empty_slot].add_item(
                    objects_info.get_item_info(info="obj_id", name=name), extra_count)
                return

    def can_add_item(self, name : str, count : int) -> bool:
        """Check whether the requested item fits

        :param name: item name
        :type name: str
        :param count: item count
        :type count: int
        :return: whether the item fits
        :rtype: bool
        """
        first_non_full_slot = self._find_first_non_full_slot(name)
        if first_non_full_slot is None:
            # no items of this type
            first_empty_slot = self._find_first_empty_slot()
            if first_empty_slot is None:
                return False
            else:
                return True
        else:
            # add item to existing stack and possibly fill new slot
            if (self.slots[first_non_full_slot].count + count <=
                    objects_info.get_item_info(info="stack_size", name=name)):
                return True
            first_empty_slot = self._find_first_empty_slot()
            if first_empty_slot is None:
                return False
            else:
                return True

    def consume_item(self, name : str, count : int) -> bool:
        """Consume item as if crafting

        :param name: item name
        :type name: str
        :param count: item count
        :type count: int
        :return: whether there are enough items
        :rtype: bool
        """
        while count > 0:
            first_slot = self.find_first_slot(name)
            if first_slot is None:
                return False
            if count < self.slots[first_slot].count:
                self.slots[first_slot].count -= count
                count = 0
            else:
                count -= self.slots[first_slot].count
                self.slots[first_slot].reset()
        return True

    def simulate_consume_item(self, name : str, count : int) -> bool:
        """Similar to consume_item, but can be reversed with revert_simulation and must be finished with finish_simulation

        :param name: item name
        :type name: str
        :param count: item count
        :type count: int
        :return: whether the simulation is possible
        :rtype: bool
        """
        while count > 0:
            first_slot = self.find_first_slot(name)
            if first_slot is None:
                return False
            if count < self.slots[first_slot].count:
                self.slots[first_slot].count -= count
                self._list_of_changes.append((first_slot, self.slots[first_slot].object.id, count))
                count = 0
            else:
                count -= self.slots[first_slot].count
                self._list_of_changes.append(
                    (first_slot, self.slots[first_slot].object.id, self.slots[first_slot].count))
                self.slots[first_slot].reset()
        return True

    def revert_simulation(self) -> None:
        """Revert simulation
        """
        for change in self._list_of_changes:
            self.slots[change[0]].add_item(change[1], change[2])
        self._list_of_changes = []

    def finish_simulation(self) -> None:
        """Finish simulation
        """
        self._list_of_changes = []

    def craft(self, name : str) -> None:
        """Craft item

        :param name: name of the item to be crafted
        :type name: str
        """
        if len(self._list_of_changes) > 0:
            raise Exception("New simulation without clearing the past one up!")
        recipe = objects_info.get_item_info(info="crafting_recipe", name=name)
        for obj_id, count in recipe:
            if not self.simulate_consume_item(
                    objects_info.get_item_info(info="name", obj_id=obj_id), count):
                self.revert_simulation()
                raise Exception("Can't craft, not enough materials!")
        if self.can_add_item(name, 1):
            self.finish_simulation()
            self.add_item(name, 1)
        else:
            self.revert_simulation()
            raise Exception("Can't craft, not enough inventory space!")

    def can_craft(self, name : str) -> bool:
        """Check if we can craft some item

        :param name: name of the item to be crafted
        :type name: str
        :return: whether it is possible
        :rtype: bool
        """
        if len(self._list_of_changes) > 0:
            raise Exception("New simulation without clearing the past one up!")
        recipe = objects_info.get_item_info(info="crafting_recipe", name=name)
        for obj_id, count in recipe:
            if not self.simulate_consume_item(
                    objects_info.get_item_info(info="name", obj_id=obj_id), count):
                self.revert_simulation()
                return False
        self.revert_simulation()
        return self.can_add_item(name, 1)

    def drop_slot(self, slot_name : str | int) -> None:
        """Drop slot contents (like dropping it on the ground)

        :param slot_name: 0-14, "Head", "Body" or "Hand"
        :type slot_name: str | int
        """
        slot = self._get_slot(slot_name)
        slot.reset()

    def unequip_slot(self, slot_name : str) -> None:
        """Unequip equip slot

        :param slot_name: "Head", "Body" or "Hand"
        :type slot_name: str
        """
        if slot_name == "Head":
            # if there is no previous slot or
            # if the slot the item should return to is occupied, we choose the first free slot
            if self.head_return_to is None or self.head_return_to.get_slot_info()[0] is not None:
                self.head_return_to = self.slots[self._find_first_empty_slot()]
            self.head_return_to.trade_slot(self.slots["Head"])
        elif slot_name == "Body":
            # if there is no previous slot or
            # if the slot the item should return to is occupied, we choose the first free slot
            if self.body_return_to is None or self.body_return_to.get_slot_info()[0] is not None:
                self.body_return_to = self.slots[self._find_first_empty_slot()]
            self.body_return_to.trade_slot(self.slots["Body"])
        elif slot_name == "Hand":
            # if there is no previous slot or
            # if the slot the item should return to is occupied, we choose the first free slot
            if self.hand_return_to is None or self.hand_return_to.get_slot_info()[0] is not None:
                self.hand_return_to = self.slots[self._find_first_empty_slot()]
            self.hand_return_to.trade_slot(self.slots["Hand"])
        
    def trade_slots(self, slot1 : InventorySlot, slot2 : InventorySlot) -> None:
        """Trade slot contents

        :param slot_name_1: inventory slot
        :type slot_name_1: InventorySlot
        :param slot_name_2: inventory slot
        :type slot_name_2: InventorySlot
        """
        if slot1.position in ["Head", "Body", "Hand"]:
            self._trade_with_equip_slot(slot1, slot2)
        elif slot2.position in ["Head", "Body", "Hand"]:
            self._trade_with_equip_slot(slot2, slot1)
        else:
            slot1.trade_slot(slot2)

    def _trade_with_equip_slot(self, equip_slot : InventorySlot, other_slot : InventorySlot) -> None:
        """Trade with equip slot

        :param equip_slot: inventory slot corresponding to "Head", "Body" or "Hand"
        :type equip_slot: InventorySlot
        :param other_slot: inventory slot corresponding to 0-14 slots
        :type other_slot: InventorySlot
        """
        if equip_slot.position not in ["Head", "Body", "Hand"]:
            raise ValueError("equip_slot is not an equipment slot!")
        if other_slot.position not in ["Head", "Body", "Hand"]:
            raise ValueError("other_slot is an equipment slot!")
        if other_slot.get_slot_info() is not None:
            if equip_slot.position == "Head":
                self.head_return_to = other_slot
            if equip_slot.position == "Body":
                self.body_return_to = other_slot
            if equip_slot.position == "Hand":
                self.hand_return_to = other_slot
        equip_slot.trade_slot(other_slot)

    # equipping in either head, body or hand slot
    # when unequipping, the unequipped item tries to return to the position it was before
    # if it's occupied, the item goes to the 1st empty slot
    def equip_item(self, name : str) -> None:
        """Equip item

        :param name: name of the item to be equipped
        :type name: str
        """
        if objects_info.get_item_info(info="equip_slot", name=name) is None:
            raise ValueError("Item is not equippable")
        item_slot = self.find_first_slot(name)
        if item_slot is None:
            raise ValueError("Can't equip item that's not in the inventory")
        item_slot = self.slots[item_slot]
        slot_name = objects_info.get_item_info(info="equip_slot", name=name)
        equip_slot = self._get_slot(slot_name)
        # prev_equip is the equipment previously equipped
        prev_equip = equip_slot.get_slot_info()
        if prev_equip is None:
            self.trade_slots(item_slot, equip_slot)
        else:
            obj, count = item_slot.get_slot_info()
            item_slot.reset()
            self.unequip_slot(slot_name)
            if slot_name == "Head":
                self.head_return_to = item_slot
            elif slot_name == "Body":
                self.body_return_to = item_slot
            elif slot_name == "Hand":
                self.hand_return_to = item_slot
            self.slots[equip_slot.position].change_item(obj.id, count)
        

    def get_inventory_slots(self) -> dict:
        """Get inventory slots

        :return: inventory slots and items equipped on head, bosy and hand slots
        :rtype: dict
        """
        return self.slots

    def update(self, dt : float):
        """Update inventory

        :param dt: dt
        :type dt: float
        """
        for slot_name, slot in self.slots.items():
            # if the slot is a normal inventory slot
            if type(slot_name) == int:
                if slot.object is not None:
                    if (objects_info.get_item_info(info="spoil_time",
                                                obj_id=slot.object.id) is not None):
                        slot.object.spoilage -= GameTime(seconds=dt)
                        if slot.object.spoilage <= GameTime(seconds=0):
                            slot.object.rot()
            # if the slot is a equipment slot
            elif type(slot_name) == str:
                if slot.object is not None:
                    if (objects_info.get_item_info(info="use_time",
                                                obj_id=slot.object.id) is not None):
                        slot.object.time_left -= GameTime(seconds=dt)
                        if slot.object.time_left <= GameTime(seconds=0):
                            equip_id = slot.object.id
                            slot.no_durability()
                            # try to replace the item if it was consumed
                            if slot.object is None:
                                first_slot = self.find_first_slot(
                                    objects_info.get_item_info(info="name", obj_id=equip_id))
                                if first_slot is not None:
                                    self.trade_slots(self.slots[first_slot], slot)
            else:
                raise Exception("Invalid slot name!")
