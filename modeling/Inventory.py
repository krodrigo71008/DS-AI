from typing import List

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
        }
        self.head = InventorySlot("Head")
        # the return_to attributes identify to where the currently equipped object should go when unequipped
        self.head_return_to : InventorySlot = None
        self.body = InventorySlot("Body")
        self.body_return_to : InventorySlot = None
        self.hand = InventorySlot("Hand")
        self.hand_return_to : InventorySlot = None
        self.equipment_slots = [self.head, self.body, self.hand]
        self._list_of_changes = []

    def get_inventory_count(self, object_names: List[str]) -> List[int]:
        """
        Get how many of a certain item we have in our inventory
        :param object_names: list of object names in Pascal Case
        :type object_names: List[str]
        :return: count of the requested objects
        :rtype: List[int]
        """
        inv = {}
        for key, value in self.slots.items():
            if value.object is not None:
                if value.object.name in inv:
                    inv[value.object.name] += value.count
                else:
                    inv[value.object.name] = value.count

        for slot in [self.head, self.body, self.hand]:
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

    # returns None if there's none
    def _find_first_empty_slot(self):
        for i in range(15):
            if self.slots[i].object is None:
                return i
        return None

    # finds slot according to the item name, returns None if there's none
    def _find_first_non_full_slot(self, name):
        for i in range(15):
            if (self.slots[i].object is not None and
                    self.slots[i].object.id == objects_info.get_item_info(info="obj_id", name=name) and
                    not self.slots[i].is_full()):
                return i
        return None

    # finds slot according to the item name, returns None if there's none
    def _find_first_slot(self, name):
        for i in range(15):
            if (self.slots[i].object is not None and
                    self.slots[i].object.id == objects_info.get_item_info(info="obj_id", name=name)):
                return i
        return None

    # Head, Body, Hand or a number in the range 0-14
    def _get_slot(self, slot_descriptor : str) -> InventorySlot:
        if slot_descriptor == "Head":
            return self.head
        elif slot_descriptor == "Body":
            return self.body
        elif slot_descriptor == "Hand":
            return self.hand
        else:
            return self.slots[slot_descriptor]

    # as in picking up an item, returns false if item doesn't fit (there's
    # something on cursor after picking it up)
    def add_item(self, name, count):
        equip_slot = objects_info.get_item_info(info="equip_slot", name=name)
        if equip_slot is not None:
            if count != 1:
                raise Exception("Incorrect usage, equippable items can't be stacked")
            if equip_slot == "Head":
                if self.head.object is None:
                    self.head.add_item(objects_info.get_item_info(info="obj_id", name=name), count)
                    return True
            elif equip_slot == "Body":
                if self.body.object is None:
                    self.body.add_item(objects_info.get_item_info(info="obj_id", name=name), count)
                    return True
            else:
                if self.hand.object is None:
                    self.hand.add_item(objects_info.get_item_info(info="obj_id", name=name), count)
                    return True
        first_non_full_slot = self._find_first_non_full_slot(name)
        if first_non_full_slot is None:
            # no items of this type or only full stacks
            first_empty_slot = self._find_first_empty_slot()
            if first_empty_slot is None:
                return False
            else:
                self.slots[first_empty_slot].add_item(
                    objects_info.get_item_info(info="obj_id", name=name), count)
                return True
        else:
            # add item to existing stack and possibly fill new slot
            if (self.slots[first_non_full_slot].count + count <=
                    objects_info.get_item_info(info="stack_size", name=name)):
                self.slots[first_non_full_slot].add_item(
                    objects_info.get_item_info(info="obj_id", name=name), count)
                return True
            self.slots[first_non_full_slot].add_item(
                objects_info.get_item_info(info="obj_id", name=name), count)
            first_empty_slot = self._find_first_empty_slot()
            if first_empty_slot is None:
                return False
            else:
                self.slots[first_empty_slot].add_item(
                    objects_info.get_item_info(info="obj_id", name=name), count)
                return True

    # just checking if it is possible to add an item
    def can_add_item(self, name, count):
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

    # consume an item like eating, returns false if there aren't enough items
    def consume_item(self, name, count):
        while count > 0:
            first_slot = self._find_first_slot(name)
            if first_slot is None:
                return False
            if count < self.slots[first_slot].count:
                self.slots[first_slot].count -= count
                count = 0
            else:
                count -= self.slots[first_slot].count
                self.slots[first_slot].reset()
        return True

    # similar to consume_item, but can be reversed with
    # revert_simulation and must be finished with finish_simulation
    def simulate_consume_item(self, name, count):
        while count > 0:
            first_slot = self._find_first_slot(name)
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

    def revert_simulation(self):
        for change in self._list_of_changes:
            self.slots[change[0]].add_item(change[1], change[2])
        self._list_of_changes = []

    def finish_simulation(self):
        self._list_of_changes = []

    # crafting, returns false if there aren't enough materials or if there isn't space
    # in the inventory (no free slots, even after materials consumption)
    def craft(self, name):
        if len(self._list_of_changes) > 0:
            raise Exception("New simulation without clearing the past one up!")
        recipe = objects_info.get_item_info(info="crafting_recipe", name=name)
        for obj_id, count in recipe:
            if not self.simulate_consume_item(
                    objects_info.get_item_info(info="name", obj_id=obj_id), count):
                self.revert_simulation()
                return False
        if self.can_add_item(name, 1):
            self.finish_simulation()
            self.add_item(name, 1)
            return True
        else:
            self.revert_simulation()
            return False

    # checking if crafting is possible
    def can_craft(self, name):
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

    # something like dropping something on the ground, does not mean "is the slot empty?"
    # slot should be a number from 0 to 14, "Head", "Body" or "Hand"
    def empty_slot(self, slot_name):
        slot = self._get_slot(slot_name)
        slot.reset()

    # trading one slot with another
    # slot should be a number from 0 to 14, "head", "body" or "hand"
    # if trading with head, body or hand, this means clicking on one,
    # then on the other, then clicking on one again, not right clicking
    def trade_slots(self, slot_name_1, slot_name_2):
        slot1 = self._get_slot(slot_name_1)
        slot2 = self._get_slot(slot_name_2)
        if slot1.position in ["Head", "Body", "Hand"] or slot2.position in ["Head", "Body", "Hand"]:
            self.trade_with_equip_slot(slot1, slot2)
        else:
            slot1.trade_slot(slot2)

    def trade_with_equip_slot(self, slot1 : InventorySlot, slot2 : InventorySlot) -> None:
        if slot2.get_slot_info() is not None:
            if slot1.position == "Head":
                self.head_return_to = slot2
            if slot1.position == "Body":
                self.body_return_to = slot2
            if slot1.position == "Hand":
                self.hand_return_to = slot2
        if slot1.get_slot_info() is not None:
            if slot2.position == "Head":
                self.head_return_to = slot1
            if slot2.position == "Body":
                self.body_return_to = slot1
            if slot2.position == "Hand":
                self.hand_return_to = slot1
        slot1.trade_slot(slot2)

    # equipping in either head, body or hand slot
    # when unequipping, the unequipped item tries to return to the position it was before
    # if it's occupied, the item goes to the 1st empty slot
    def equip_item(self, name):
        if objects_info.get_item_info(info="equip_slot", name=name) is None:
            raise Exception("Item is not equippable")
        item_slot = self._find_first_slot(name)
        if item_slot is None:
            raise Exception("Can't equip item that's not in the inventory")
        item_slot = self.slots[item_slot]
        equip_slot = self._get_slot(objects_info.get_item_info(info="equip_slot", name=name))
        # prev_equip is the
        prev_equip = equip_slot.get_slot_info()
        if prev_equip is None:
            item_slot.trade_slot(equip_slot)
        else:
            obj, count = item_slot.get_slot_info()
            item_slot.reset()
            if equip_slot.position == "Head":
                # if there is no previous slot or
                # if the slot the item should return to is occupied, we choose the first free slot
                if self.head_return_to is None or self.head_return_to.get_slot_info() is not None:
                    self.head_return_to = self.slots[self._find_first_empty_slot()]
                self.trade_with_equip_slot(self.head_return_to, self.head)
                self.head.change_item(obj.id, count)
            if equip_slot.position == "Body":
                # if there is no previous slot or
                # if the slot the item should return to is occupied, we choose the first free slot
                if self.body_return_to is None or self.body_return_to.get_slot_info() is not None:
                    self.body_return_to = self.slots[self._find_first_empty_slot()]
                self.trade_with_equip_slot(self.body_return_to, self.head)
                self.body.change_item(obj.id, count)
            if equip_slot.position == "Hand":
                # if there is no previous slot or
                # if the slot the item should return to is occupied, we choose the first free slot
                if self.hand_return_to is None or self.hand_return_to.get_slot_info() is not None:
                    self.hand_return_to = self.slots[self._find_first_empty_slot()]
                self.trade_with_equip_slot(self.hand_return_to, self.head)
                self.hand.change_item(obj.id, count)

    def update(self, dt):
        for slot in self.slots.values():
            if slot.object is not None:
                if (objects_info.get_item_info(info="spoil_time",
                                               obj_id=slot.object.id) is not None):
                    slot.object.spoilage -= GameTime(seconds=dt)
                    if slot.object.spoilage <= GameTime(seconds=0):
                        slot.object.rot()

        for slot in self.equipment_slots:
            if slot.object is not None:
                if (objects_info.get_item_info(info="use_time",
                                               obj_id=slot.object.id) is not None):
                    slot.object.time_left -= GameTime(seconds=dt)
                    if slot.object.time_left <= GameTime(seconds=0):
                        equip_id = slot.object.id
                        slot.no_durability()
                        # try to replace the item if it was consumed
                        if slot.object is None:
                            first_slot = self._find_first_slot(
                                objects_info.get_item_info(info="name", obj_id=equip_id))
                            if first_slot is not None:
                                self.trade_with_equip_slot(self.slots[first_slot], slot)
