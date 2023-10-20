import random

import pytest

from modeling.Inventory import Inventory
from modeling.ObjectsInfo import objects_info
from utility.GameTime import GameTime

add_objects_test_cases = [
    ([], {
        0: (None, 0),
        1: (None, 0),
        2: (None, 0),
        3: (None, 0),
        4: (None, 0),
        5: (None, 0),
        6: (None, 0),
        7: (None, 0),
        8: (None, 0),
        9: (None, 0),
        10: (None, 0),
        11: (None, 0),
        12: (None, 0),
        13: (None, 0),
        14: (None, 0),
        "Head": (None, 0),
        "Body": (None, 0),
        "Hand": (None, 0),
    }),
    ([("CutGrass", 1)], {
        0: ("CutGrass", 1),
        1: (None, 0),
        2: (None, 0),
        3: (None, 0),
        4: (None, 0),
        5: (None, 0),
        6: (None, 0),
        7: (None, 0),
        8: (None, 0),
        9: (None, 0),
        10: (None, 0),
        11: (None, 0),
        12: (None, 0),
        13: (None, 0),
        14: (None, 0),
        "Head": (None, 0),
        "Body": (None, 0),
        "Hand": (None, 0),
    }),
    ([("Axe", 1)], {
        0: (None, 0),
        1: (None, 0),
        2: (None, 0),
        3: (None, 0),
        4: (None, 0),
        5: (None, 0),
        6: (None, 0),
        7: (None, 0),
        8: (None, 0),
        9: (None, 0),
        10: (None, 0),
        11: (None, 0),
        12: (None, 0),
        13: (None, 0),
        14: (None, 0),
        "Head": (None, 0),
        "Body": (None, 0),
        "Hand": ("Axe", 1),
    }),
    ([("Axe", 1), ("Torch", 1)], {
        0: ("Torch", 1),
        1: (None, 0),
        2: (None, 0),
        3: (None, 0),
        4: (None, 0),
        5: (None, 0),
        6: (None, 0),
        7: (None, 0),
        8: (None, 0),
        9: (None, 0),
        10: (None, 0),
        11: (None, 0),
        12: (None, 0),
        13: (None, 0),
        14: (None, 0),
        "Head": (None, 0),
        "Body": (None, 0),
        "Hand": ("Axe", 1),
    }),
    ([("Torch", 1), ("Torch", 1), ("CutGrass", 1)], {
        0: ("Torch", 1),
        1: ("CutGrass", 1),
        2: (None, 0),
        3: (None, 0),
        4: (None, 0),
        5: (None, 0),
        6: (None, 0),
        7: (None, 0),
        8: (None, 0),
        9: (None, 0),
        10: (None, 0),
        11: (None, 0),
        12: (None, 0),
        13: (None, 0),
        14: (None, 0),
        "Head": (None, 0),
        "Body": (None, 0),
        "Hand": ("Torch", 1),
    }),
    ([("CutGrass", 39), ("Torch", 1), ("Torch", 1), ("CutGrass", 1)], {
        0: ("CutGrass", 40),
        1: ("Torch", 1),
        2: (None, 0),
        3: (None, 0),
        4: (None, 0),
        5: (None, 0),
        6: (None, 0),
        7: (None, 0),
        8: (None, 0),
        9: (None, 0),
        10: (None, 0),
        11: (None, 0),
        12: (None, 0),
        13: (None, 0),
        14: (None, 0),
        "Head": (None, 0),
        "Body": (None, 0),
        "Hand": ("Torch", 1),
    }),
    ([("CutGrass", 39), ("Torch", 1), ("Torch", 1), ("CutGrass", 3)], {
        0: ("CutGrass", 40),
        1: ("Torch", 1),
        2: ("CutGrass", 2),
        3: (None, 0),
        4: (None, 0),
        5: (None, 0),
        6: (None, 0),
        7: (None, 0),
        8: (None, 0),
        9: (None, 0),
        10: (None, 0),
        11: (None, 0),
        12: (None, 0),
        13: (None, 0),
        14: (None, 0),
        "Head": (None, 0),
        "Body": (None, 0),
        "Hand": ("Torch", 1),
    }),
    ([("CutGrass", 34), ("Twigs", 30), ("Twigs", 5), ("CutGrass", 13)], {
        0: ("CutGrass", 40),
        1: ("Twigs", 35),
        2: ("CutGrass", 7),
        3: (None, 0),
        4: (None, 0),
        5: (None, 0),
        6: (None, 0),
        7: (None, 0),
        8: (None, 0),
        9: (None, 0),
        10: (None, 0),
        11: (None, 0),
        12: (None, 0),
        13: (None, 0),
        14: (None, 0),
        "Head": (None, 0),
        "Body": (None, 0),
        "Hand": (None, 0),
    }),
]

@pytest.mark.parametrize("test_case", add_objects_test_cases)
def test_add_objects(test_case):
    # test_case[0] is [(obj, count)] to be added to the inventory
    # test_case[1] is expected result
    inv = Inventory()
    if len(test_case[0]) > 0:
        for obj, count in test_case[0]:
            inv.add_item(obj, count)
    cur_slots = inv.get_inventory_slots()
    for slot_name in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, "Head", "Body", "Hand"]:
        if cur_slots[slot_name].object is None:
            assert test_case[1][slot_name][0] is None
        else:
            assert test_case[1][slot_name][0] is not None
            assert cur_slots[slot_name].object.name == test_case[1][slot_name][0]
            assert cur_slots[slot_name].count == test_case[1][slot_name][1]

add_remove_objects_test_cases = [
    ([("add", ("CutGrass", 1)), ("consume", ("CutGrass", 1))], {
        0: (None, 0),
        1: (None, 0),
        2: (None, 0),
        3: (None, 0),
        4: (None, 0),
        5: (None, 0),
        6: (None, 0),
        7: (None, 0),
        8: (None, 0),
        9: (None, 0),
        10: (None, 0),
        11: (None, 0),
        12: (None, 0),
        13: (None, 0),
        14: (None, 0),
        "Head": (None, 0),
        "Body": (None, 0),
        "Hand": (None, 0),
    }),
    ([("add", ("CutGrass", 2)), ("consume", ("CutGrass", 1))], {
        0: ("CutGrass", 1),
        1: (None, 0),
        2: (None, 0),
        3: (None, 0),
        4: (None, 0),
        5: (None, 0),
        6: (None, 0),
        7: (None, 0),
        8: (None, 0),
        9: (None, 0),
        10: (None, 0),
        11: (None, 0),
        12: (None, 0),
        13: (None, 0),
        14: (None, 0),
        "Head": (None, 0),
        "Body": (None, 0),
        "Hand": (None, 0),
    }),
    ([("add", ("CutGrass", 2)), ("add", ("Twigs", 2)), ("consume", ("CutGrass", 2))], {
        0: (None, 0),
        1: ("Twigs", 2),
        2: (None, 0),
        3: (None, 0),
        4: (None, 0),
        5: (None, 0),
        6: (None, 0),
        7: (None, 0),
        8: (None, 0),
        9: (None, 0),
        10: (None, 0),
        11: (None, 0),
        12: (None, 0),
        13: (None, 0),
        14: (None, 0),
        "Head": (None, 0),
        "Body": (None, 0),
        "Hand": (None, 0),
    }),
    ([("add", ("CutGrass", 20)), ("add", ("Twigs", 2)), ("add", ("CutGrass", 30)), ("consume", ("CutGrass", 45))], {
        0: (None, 0),
        1: ("Twigs", 2),
        2: ("CutGrass", 5),
        3: (None, 0),
        4: (None, 0),
        5: (None, 0),
        6: (None, 0),
        7: (None, 0),
        8: (None, 0),
        9: (None, 0),
        10: (None, 0),
        11: (None, 0),
        12: (None, 0),
        13: (None, 0),
        14: (None, 0),
        "Head": (None, 0),
        "Body": (None, 0),
        "Hand": (None, 0),
    }),
    ([("add", ("CutGrass", 2)), ("add", ("Twigs", 2)), ("add", ("CutGrass", 39)), ("consume", ("CutGrass", 40))], {
        0: (None, 0),
        1: ("Twigs", 2),
        2: ("CutGrass", 1),
        3: (None, 0),
        4: (None, 0),
        5: (None, 0),
        6: (None, 0),
        7: (None, 0),
        8: (None, 0),
        9: (None, 0),
        10: (None, 0),
        11: (None, 0),
        12: (None, 0),
        13: (None, 0),
        14: (None, 0),
        "Head": (None, 0),
        "Body": (None, 0),
        "Hand": (None, 0),
    }),
    ([("add", ("CutGrass", 1)), ("add", ("Twigs", 1)), ("drop", 0)], {
        0: (None, 0),
        1: ("Twigs", 1),
        2: (None, 0),
        3: (None, 0),
        4: (None, 0),
        5: (None, 0),
        6: (None, 0),
        7: (None, 0),
        8: (None, 0),
        9: (None, 0),
        10: (None, 0),
        11: (None, 0),
        12: (None, 0),
        13: (None, 0),
        14: (None, 0),
        "Head": (None, 0),
        "Body": (None, 0),
        "Hand": (None, 0),
    }),
    ([("add", ("CutGrass", 40)), ("add", ("CutGrass", 40)), ("add", ("Twigs", 4)), ("drop", 0), ("add", ("Twigs", 39)), ], {
        0: ("Twigs", 3),
        1: ("CutGrass", 40),
        2: ("Twigs", 40),
        3: (None, 0),
        4: (None, 0),
        5: (None, 0),
        6: (None, 0),
        7: (None, 0),
        8: (None, 0),
        9: (None, 0),
        10: (None, 0),
        11: (None, 0),
        12: (None, 0),
        13: (None, 0),
        14: (None, 0),
        "Head": (None, 0),
        "Body": (None, 0),
        "Hand": (None, 0),
    }),
    ([("add", ("Torch", 1))], {
        0: (None, 0),
        1: (None, 0),
        2: (None, 0),
        3: (None, 0),
        4: (None, 0),
        5: (None, 0),
        6: (None, 0),
        7: (None, 0),
        8: (None, 0),
        9: (None, 0),
        10: (None, 0),
        11: (None, 0),
        12: (None, 0),
        13: (None, 0),
        14: (None, 0),
        "Head": (None, 0),
        "Body": (None, 0),
        "Hand": ("Torch", 1),
    }),
    ([("add", ("Torch", 1)), ("add", ("Torch", 1)), ("add", ("Torch", 1)), ("drop", 0)], {
        0: (None, 0),
        1: ("Torch", 1),
        2: (None, 0),
        3: (None, 0),
        4: (None, 0),
        5: (None, 0),
        6: (None, 0),
        7: (None, 0),
        8: (None, 0),
        9: (None, 0),
        10: (None, 0),
        11: (None, 0),
        12: (None, 0),
        13: (None, 0),
        14: (None, 0),
        "Head": (None, 0),
        "Body": (None, 0),
        "Hand": ("Torch", 1),
    }),
]

@pytest.mark.parametrize("test_case", add_remove_objects_test_cases)
def test_add_remove_objects(test_case):
    # test_case[0] is a list of (action, (obj, count))
    # test_case[1] is expected result
    inv = Inventory()
    if len(test_case[0]) > 0:
        for action, payload in test_case[0]:
            if action == "add":
                name, count = payload
                inv.add_item(name, count)
            elif action == "consume":
                name, count = payload
                inv.consume_item(name, count)
            elif action == "drop":
                slot_name = payload
                inv.drop_slot(slot_name)
    cur_slots = inv.get_inventory_slots()
    for slot_name in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, "Head", "Body", "Hand"]:
        if cur_slots[slot_name].object is None:
            assert test_case[1][slot_name][0] is None
        else:
            assert test_case[1][slot_name][0] is not None
            assert cur_slots[slot_name].object.name == test_case[1][slot_name][0]
            assert cur_slots[slot_name].count == test_case[1][slot_name][1]

crafting_test_cases = [
    ([("add", ("CutGrass", 2)), ("add", ("Twigs", 2)), ("craft", "Torch")], {
        0: (None, 0),
        1: (None, 0),
        2: (None, 0),
        3: (None, 0),
        4: (None, 0),
        5: (None, 0),
        6: (None, 0),
        7: (None, 0),
        8: (None, 0),
        9: (None, 0),
        10: (None, 0),
        11: (None, 0),
        12: (None, 0),
        13: (None, 0),
        14: (None, 0),
        "Head": (None, 0),
        "Body": (None, 0),
        "Hand": ("Torch", 1),
    }),
    ([("add", ("CutGrass", 4)), ("add", ("Twigs", 4)), ("craft", "Torch"), ("craft", "Torch")], {
        0: ("Torch", 1),
        1: (None, 0),
        2: (None, 0),
        3: (None, 0),
        4: (None, 0),
        5: (None, 0),
        6: (None, 0),
        7: (None, 0),
        8: (None, 0),
        9: (None, 0),
        10: (None, 0),
        11: (None, 0),
        12: (None, 0),
        13: (None, 0),
        14: (None, 0),
        "Head": (None, 0),
        "Body": (None, 0),
        "Hand": ("Torch", 1),
    }),
    ([("add", ("CutGrass", 6)), ("add", ("Twigs", 6)), ("craft", "Torch"), ("craft", "Torch")], {
        0: ("CutGrass", 2),
        1: ("Twigs", 2),
        2: ("Torch", 1),
        3: (None, 0),
        4: (None, 0),
        5: (None, 0),
        6: (None, 0),
        7: (None, 0),
        8: (None, 0),
        9: (None, 0),
        10: (None, 0),
        11: (None, 0),
        12: (None, 0),
        13: (None, 0),
        14: (None, 0),
        "Head": (None, 0),
        "Body": (None, 0),
        "Hand": ("Torch", 1),
    }),
    ([("add", ("CutGrass", 8)), ("add", ("Twigs", 6)), ("add", ("CutGrass", 37)), ("drop", 0), ("craft", "Torch"), ("craft", "Torch")], {
        0: ("Torch", 1),
        1: ("Twigs", 2),
        2: ("CutGrass", 1),
        3: (None, 0),
        4: (None, 0),
        5: (None, 0),
        6: (None, 0),
        7: (None, 0),
        8: (None, 0),
        9: (None, 0),
        10: (None, 0),
        11: (None, 0),
        12: (None, 0),
        13: (None, 0),
        14: (None, 0),
        "Head": (None, 0),
        "Body": (None, 0),
        "Hand": ("Torch", 1),
    }),
]

@pytest.mark.parametrize("test_case", crafting_test_cases)
def test_crafting(test_case):
    # test_case[0] is a list of (action, (obj, count))
    # test_case[1] is expected result
    inv = Inventory()
    if len(test_case[0]) > 0:
        for action, payload in test_case[0]:
            if action == "add":
                name, count = payload
                inv.add_item(name, count)
            elif action == "consume":
                name, count = payload
                inv.consume_item(name, count)
            elif action == "drop":
                slot_name = payload
                inv.drop_slot(slot_name)
            elif action == "craft":
                item = payload
                inv.craft(item)
    cur_slots = inv.get_inventory_slots()
    for slot_name in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, "Head", "Body", "Hand"]:
        if cur_slots[slot_name].object is None:
            assert test_case[1][slot_name][0] is None
        else:
            assert test_case[1][slot_name][0] is not None
            assert cur_slots[slot_name].object.name == test_case[1][slot_name][0]
            assert cur_slots[slot_name].count == test_case[1][slot_name][1]

equip_test_cases = [
    ([("add", ("CutGrass", 2)), ("add", ("Twigs", 2)), ("add", ("Torch", 1)), ("unequip", "Hand")], {
        0: ("CutGrass", 2),
        1: ("Twigs", 2),
        2: ("Torch", 1),
        3: (None, 0),
        4: (None, 0),
        5: (None, 0),
        6: (None, 0),
        7: (None, 0),
        8: (None, 0),
        9: (None, 0),
        10: (None, 0),
        11: (None, 0),
        12: (None, 0),
        13: (None, 0),
        14: (None, 0),
        "Head": (None, 0),
        "Body": (None, 0),
        "Hand": (None, 0),
    }),
    ([("add", ("CutGrass", 2)), ("add", ("Twigs", 2)), ("add", ("Torch", 1)), ("unequip", "Hand"), ("drop", 0), ("equip", "Torch"), 
            ("unequip", "Hand")], {
        0: (None, 0),
        1: ("Twigs", 2),
        2: ("Torch", 1),
        3: (None, 0),
        4: (None, 0),
        5: (None, 0),
        6: (None, 0),
        7: (None, 0),
        8: (None, 0),
        9: (None, 0),
        10: (None, 0),
        11: (None, 0),
        12: (None, 0),
        13: (None, 0),
        14: (None, 0),
        "Head": (None, 0),
        "Body": (None, 0),
        "Hand": (None, 0),
    }),
    ([("add", ("CutGrass", 2)), ("add", ("Twigs", 2)), ("add", ("Torch", 1)), ("unequip", "Hand"), ("drop", 0), ("equip", "Torch"), 
            ("unequip", "Hand"), ("add", ("Torch", 1)), ("unequip", "Hand")], {
        0: ("Torch", 1),
        1: ("Twigs", 2),
        2: ("Torch", 1),
        3: (None, 0),
        4: (None, 0),
        5: (None, 0),
        6: (None, 0),
        7: (None, 0),
        8: (None, 0),
        9: (None, 0),
        10: (None, 0),
        11: (None, 0),
        12: (None, 0),
        13: (None, 0),
        14: (None, 0),
        "Head": (None, 0),
        "Body": (None, 0),
        "Hand": (None, 0),
    }),
    ([("add", ("Torch", 1)), ("unequip", "Hand"), ("equip", "Torch"), ("add", ("Twigs", 1)), ("unequip", "Hand")], {
        0: ("Twigs", 1),
        1: ("Torch", 1),
        2: (None, 0),
        3: (None, 0),
        4: (None, 0),
        5: (None, 0),
        6: (None, 0),
        7: (None, 0),
        8: (None, 0),
        9: (None, 0),
        10: (None, 0),
        11: (None, 0),
        12: (None, 0),
        13: (None, 0),
        14: (None, 0),
        "Head": (None, 0),
        "Body": (None, 0),
        "Hand": (None, 0),
    }),
    ([("add", ("CutGrass", 1)), ("add", ("Torch", 1)), ("unequip", "Hand"), ("equip", "Torch"), ("add", ("Twigs", 1)), ("unequip", "Hand")], {
        0: ("CutGrass", 1),
        1: ("Twigs", 1),
        2: ("Torch", 1),
        3: (None, 0),
        4: (None, 0),
        5: (None, 0),
        6: (None, 0),
        7: (None, 0),
        8: (None, 0),
        9: (None, 0),
        10: (None, 0),
        11: (None, 0),
        12: (None, 0),
        13: (None, 0),
        14: (None, 0),
        "Head": (None, 0),
        "Body": (None, 0),
        "Hand": (None, 0),
    }),
    ([("add", ("CutGrass", 1)), ("add", ("Torch", 1)), ("unequip", "Hand"), ("equip", "Torch"), ("add", ("Twigs", 1)), ("drop", 0), ("unequip", "Hand")], {
        0: ("Torch", 1),
        1: ("Twigs", 1),
        2: (None, 0),
        3: (None, 0),
        4: (None, 0),
        5: (None, 0),
        6: (None, 0),
        7: (None, 0),
        8: (None, 0),
        9: (None, 0),
        10: (None, 0),
        11: (None, 0),
        12: (None, 0),
        13: (None, 0),
        14: (None, 0),
        "Head": (None, 0),
        "Body": (None, 0),
        "Hand": (None, 0),
    }),
]

@pytest.mark.parametrize("test_case", equip_test_cases)
def test_equipping_unequipping(test_case):
    # test_case[0] is a list of (action, (obj, count))
    # test_case[1] is expected result
    inv = Inventory()
    if len(test_case[0]) > 0:
        for action, payload in test_case[0]:
            if action == "add":
                name, count = payload
                inv.add_item(name, count)
            elif action == "consume":
                name, count = payload
                inv.consume_item(name, count)
            elif action == "drop":
                slot_name = payload
                inv.drop_slot(slot_name)
            elif action == "equip":
                obj_name = payload
                inv.equip_item(obj_name)
            elif action == "unequip":
                slot_name = payload
                inv.unequip_slot(slot_name)
            elif action == "craft":
                item = payload
                inv.craft(item)
    cur_slots = inv.get_inventory_slots()
    for slot_name in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, "Head", "Body", "Hand"]:
        if cur_slots[slot_name].object is None:
            assert test_case[1][slot_name][0] is None
        else:
            assert test_case[1][slot_name][0] is not None
            assert cur_slots[slot_name].object.name == test_case[1][slot_name][0]
            assert cur_slots[slot_name].count == test_case[1][slot_name][1]

get_count_test_cases = [
    ([], 
        (["CutGrass"], [0])
    ),
    ([], 
        (["CutGrass", "Twigs"], [0, 0])
    ),
    ([("CutGrass", 3)],
        (["CutGrass"], [3])
    ),
    ([("CutGrass", 39), ("CutGrass", 39)],
        (["CutGrass"], [78])
    ),
    ([("Axe", 1)],
        (["Axe"], [1])
    ),
    ([("Axe", 1), ("Axe", 1)],
        (["Axe"], [2])
    ),
    ([("Axe", 1), ("CutGrass", 1), ("Axe", 1)],
        (["Axe", "CutGrass"], [2, 1])
    ),
    ([("Axe", 1), ("CutGrass", 40), ("CutGrass", 40), ("Axe", 1)],
        (["Axe", "CutGrass"], [2, 80])
    ),
    ([("Twigs", 1), ("CutGrass", 40), ("CutGrass", 40), ("Twigs", 1)],
        (["Twigs", "CutGrass"], [2, 80])
    ),
]

@pytest.mark.parametrize("test_case", get_count_test_cases)
def test_get_inventory_count(test_case):
    # test_case[0] is [(obj, count)] to add to the inventory
    # test_case[1] is (obj_list, count_list) to query
    inv = Inventory()
    if len(test_case[0]) > 0:
        for obj, count in test_case[0]:
            inv.add_item(obj, count)
    
    obj_list, count_list = test_case[1]
    assert inv.get_inventory_count(obj_list) == count_list

def test_equipment_update():
    torch_time = objects_info.get_item_info(info="use_time", name="Torch").seconds()
    inv = Inventory()
    inv.add_item("Torch", 1)
    inv.add_item("Torch", 1)
    # 1 torch on hand slot, 1 on slot 0
    inv_contents = inv.get_inventory_slots()
    assert (inv_contents["Hand"].object.name, inv_contents["Hand"].count) == ("Torch", 1)
    assert (inv_contents[0].object.name, inv_contents[0].count) == ("Torch", 1)
    inv.update(torch_time)
    inv_contents = inv.get_inventory_slots()
    assert (inv_contents["Hand"].object.name, inv_contents["Hand"].count) == ("Torch", 1)
    assert (inv_contents[0].object, inv_contents[0].count) == (None, 0)
    inv.update(torch_time)
    inv_contents = inv.get_inventory_slots()
    assert (inv_contents["Hand"].object, inv_contents["Hand"].count) == (None, 0)
    assert (inv_contents[0].object, inv_contents[0].count) == (None, 0)

def test_slot_update():
    random.seed(727)
    for _ in range(10):
        food_name, food_info = random.choice([t for t in objects_info._food_values.items()])
        spoil_time = GameTime(days=food_info[3]).seconds()
        count = random.randint(1, 5)
        inv = Inventory()
        inv.add_item(food_name, count)
        # food on slot 0
        inv_contents = inv.get_inventory_slots()
        assert (inv_contents[0].object.name, inv_contents[0].count) == (food_name, count)
        inv.update(spoil_time-1)
        inv_contents = inv.get_inventory_slots()
        assert (inv_contents[0].object.name, inv_contents[0].count) == (food_name, count)
        inv.update(1)
        inv_contents = inv.get_inventory_slots()
        assert (inv_contents[0].object.name, inv_contents[0].count) == ("Rot", count)
