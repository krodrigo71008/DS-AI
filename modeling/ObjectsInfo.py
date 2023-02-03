import pandas as pd

from utility.GameTime import GameTime


class ObjectsInfo:
    def __init__(self):
        # name refers to the object name, not the image name
        # for example: both harvested and not harvested grass are "Grass"
        self._item_table = pd.read_csv('utility/objects_info.csv')
        self._food_values = {
            "BaconAndEggs": [20, 75, 5, 15],
            "BatiliskWing": [3, 12.5, -10, 6],
            "CookedBatiliskWing": [8, 18.75, 0, 10],
            "Berries": [0, 9.375, 0, 6],
            "CookedBerries": [1, 12.5, 0, 3],
            "BlueCap": [20, 12.5, -15, 10],
            "CookedBlueCap": [-3, 0, 10, 10],
            "Butter": [40, 25, 0, 40],
            "ButterMuffin": [20, 37.5, 5, 15],
            "ButterflyWings": [8, 9.375, 0, 6],
            "Carrot": [1, 12.5, 0, 10],
            "CookedCarrot": [3, 12.5, 0, 6],
            "CaveBanana": [1, 12.5, 0, 10],
            "CookedCaveBanana": [3, 12.5, 0, 6],
            "Corn": [3, 25, 0, 10],
            "CookedCorn": [3, 12.5, 0, 15],
            "DeerclopsEyeball": [60, 75, -15, None],
            "Dragonfruit": [3, 9.375, 0, 6],
            "CookedDragonfruit": [20, 12.5, 0, 3],
            "Dragonpie": [40, 75, 5, 15],
            "Drumstick": [0, 12.5, -10, 6],
            "CookedDrumstick": [1, 12.5, 0, 10],
            "Durian": [-3, 25, -5, 10],
            "CookedDurian": [0, 25, -5, 6],
            "Eel": [3, 9.375, 0, 6],
            "CookedEel": [8, 12.5, 0, 10],
            "Egg": [0, 9.375, 0, 10],
            "CookedEgg": [0, 12.5, 0, 6],
            "Eggplant": [8, 25, 0, 10],
            "CookedEggplant": [20, 25, 0, 6],
            "Fish": [1, 12.5, 0, 3],
            "CookedFish": [1, 12.5, 0, 6],
            "FishTacos": [20, 37.5, 5, 6],
            "FishSticks": [40, 37.5, 5, 10],
            "FistFullOfJam": [3, 37.5, 5, 15],
            "FrogLegs": [0, 12.5, -10, 6],
            "CookedFrogLegs": [1, 12.5, 0, 10],
            "FroggieBunwich": [20, 37.5, 5, 15],
            "FruitMedley": [20, 25, 5, 6],
            "GlowBerry": [11, 25, -10, 10],
            "GreenCap": [0, 12.5, -50, 10],
            "CookedGreenCap": [-1, 0, 15, 10],
            "GuardiansHorn": [60, 75, -15, None],
            "Honey": [3, 9.375, 0, 40],
            "HoneyHam": [30, 75, 5, 15],
            "HoneyNuggets": [20, 37.5, 5, 15],
            "Jerky": [20, 25, 15, 20],
            "Kabobs": [3, 37.5, 5, 15],
            "KoalefantTrunk": [30, 37.5, 0, 6],
            "CookedKoalefantTrunk": [40, 75, 0, 15],
            "WinterKoalefantTrunk": [30, 37.5, 0, 6],
            "CookedWinterKoalefantTrunk": [40, 75, 0, 15],
            "LeafyMeat": [0, 12.5, 0, 6],
            "CookedLeafyMeat": [1, 18.75, 0, 10],
            "Lichen": [3, 12.5, -10, 2],
            "LightBulb": [1, 0, 0, 6],
            "Meat": [1, 25, -10, 6],
            "CookedMeat": [3, 25, 0, 10],
            "Meatballs": [3, 62.5, 5, 10],
            "MeatyStew": [12, 150, 5, 10],
            "MonsterJerky": [-3, 18.75, -5, 20],
            "MonsterLasagna": [-20, 37.5, -20, 10],
            "MonsterMeat": [-20, 18.75, -15, 6],
            "CookedMonsterMeat": [-3, 18.75, -10, 15],
            "Morsel": [0, 12.5, -10, 6],
            "CookedMorsel": [1, 12.5, 0, 10],
            "Petals": [1, 0, 0, 6],
            "Foliage": [1, 0, 0, 6],
            "DarkPetals": [0, 0, -5, 6],
            "Phlegm": [0, 12.5, -15, None],
            "Pierogi": [40, 37.5, 5, 20],
            "Pomegranate": [3, 9.375, 0, 6],
            "CookedPomegranate": [20, 12.5, 0, 3],
            "Powdercake": [-3, 0, 0, 18750],
            "Pumpkin": [3, 37.5, 0, 10],
            "CookedPumpkin": [8, 37.5, 0, 6],
            "PumpkinCookies": [0, 37.5, 15, 10],
            "Ratatouille": [3, 25, 5, 15],
            "RedCap": [-20, 12.5, 0, 10],
            "CookedRedCap": [1, 0, -10, 10],
            "Rot": [-1, -10, 0, None],
            "RottenEgg": [-1, -10, 0, None],
            "Seeds": [0, 4.6875, 0, 40],
            "CookedSeeds": [1, 4.6875, 0, 10],
            "SmallJerky": [8, 12.5, 10, 20],
            "StuffedEggplant": [3, 37.5, 5, 15],
            "TallbirdEgg": [3, 25, 0, None],
            "CookedTallbirdEgg": [0, 37.5, 0, 6],
            "Taffy": [-3, 25, 15, 15],
            "TurkeyDinner": [20, 75, 5, 6],
            "Unagi": [20, 18.75, 5, 10],
            "Waffles": [60, 37.5, 5, 6],
            "WetGoop": [0, 0, 0, 6],
        }
        self._name_to_stack = {
            "Seeds": 40,
            "Flint": 40,
            "MonsterMeat": 20,
            "HoundTooth": 40,
            "PigSkin": 40,
            "Ashes": 40,
            "Honey": 40,
            "Stinger": 40,
            "FrogLegs": 40,
            "Blueprint": 1,
            "Silk": 40,
            "Meat": 20,
            "Carrot": 40,
            "SpiderGland": 20,
            "Rocks": 40,
            "Axe": 1,
            "Pickaxe": 1,
            "Shovel": 1,
            "Hammer": 1,
            "Razor": 1,
            "Torch": 1,
            "CutGrass": 40,
            "Twigs": 40,
            "Rot": 40,
            "Berries": 40,
        }
        # this is for items with durability (axe, pickaxe, etc)
        self._name_to_max_uses = {
            "Axe": 100,
            "Pickaxe": 33,
            "Shovel": 25,
            "Hammer": 75,
        }
        # this is for items that degrade with time (like torch, lantern), use time in seconds
        self._name_to_use_time = {
            "Torch": GameTime(seconds=75)
        }
        # this is for equippable items
        self._name_to_equippable_slot = {
            "Axe": "Hand",
            "Pickaxe": "Hand",
            "Shovel": "Hand",
            "Hammer": "Hand",
            "Torch": "Hand",
        }
        self._obj_id_to_crafting_recipe = {
            31: [(32, 2), (33, 2)],
        }

    # get one of the attributes to image_id, name or obj_id, passing the current values (two of them are None)
    # example: _get_attr("image_id", None, "Rocks", None) gets the image_id of the object with name "Rocks"
    def _get_attr(self, attr_to, image_id, name, obj_id):
        if attr_to == "image_id":
            if name is not None:
                return self._item_table[self._item_table["name"] == name][attr_to].iloc[0]
            if obj_id is not None:
                return self._item_table[self._item_table["obj_id"] == obj_id][attr_to].iloc[0]
            return image_id
        if attr_to == "name":
            if image_id is not None:
                return self._item_table[self._item_table["image_id"] == image_id][attr_to].iloc[0]
            if obj_id is not None:
                return self._item_table[self._item_table["obj_id"] == obj_id][attr_to].iloc[0]
            return name
        if attr_to == "obj_id":
            if image_id is not None:
                return self._item_table[self._item_table["image_id"] == image_id][attr_to].iloc[0]
            if name is not None:
                return self._item_table[self._item_table["name"] == name][attr_to].iloc[0]
            return obj_id

    # valid values for params:
    # info: equip_slot, max_uses, use_time, stack_size, spoil_time, crafting_recipe, food_stats,
    # name, image_id, obj_id, object_type
    # there should be exactly one of the three following key arguments:
    # image_id (int), name (str) or obj_id (int)
    # example: get_item_info(info="equip_slot", image_id=60)
    def get_item_info(self, info : str, **kwargs):
        """Get item info according to the key arguments, there should be exactly one of these three key arguments: image_id, name or obj_id

        :param info: equip_slot, max_uses, use_time, stack_size, spoil_time, crafting_recipe, food_stats, name, image_id, obj_id or object_type
        :type info: str
        :return: requested info
        :rtype: it depends
        """
        if len(kwargs) != 1:
            raise ValueError("Wrong usage! Exactly one key argument should be used.")
        image_id = None
        name = None
        obj_id = None
        if "image_id" in kwargs:
            image_id = kwargs["image_id"]
        if "name" in kwargs:
            name = kwargs["name"]
        if "obj_id" in kwargs:
            obj_id = kwargs["obj_id"]
        if info == "equip_slot":
            name = self._get_attr("name", image_id, name, obj_id)
            if name in self._name_to_equippable_slot:
                return self._name_to_equippable_slot[name]
            return None
        if info == "max_uses":
            name = self._get_attr("name", image_id, name, obj_id)
            if name in self._name_to_max_uses:
                return self._name_to_max_uses[name]
            return None
        if info == "use_time":
            name = self._get_attr("name", image_id, name, obj_id)
            if name in self._name_to_use_time:
                return self._name_to_use_time[name]
            return None
        if info == "stack_size":
            name = self._get_attr("name", image_id, name, obj_id)
            if name in self._name_to_stack:
                return self._name_to_stack[name]
            return None
        # returned spoil time is in days
        if info == "spoil_time":
            name = self._get_attr("name", image_id, name, obj_id)
            if name in self._food_values:
                return GameTime(days=self._food_values[name][3])
            return None
        if info == "crafting_recipe":
            name = self._get_attr("obj_id", image_id, name, obj_id)
            if name in self._obj_id_to_crafting_recipe:
                return self._obj_id_to_crafting_recipe[name]
            return None
        # food_stats returns [health, hunger, sanity]
        if info == "food_stats":
            name = self._get_attr("name", image_id, name, obj_id)
            if name in self._food_values:
                return self._food_values[name][0:3]
            return None
        if info == "image_id":
            return self._get_attr("image_id", image_id, name, obj_id)
        if info == "name":
            return self._get_attr("name", image_id, name, obj_id)
        if info == "obj_id":
            return self._get_attr("obj_id", image_id, name, obj_id)
        if info == "object_type":
            if image_id is not None:
                return self._item_table[self._item_table["image_id"] == image_id].object_type.iloc[0]
            if name is not None:
                return self._item_table[self._item_table["name"] == name].object_type.iloc[0]
            if obj_id is not None:
                return self._item_table[self._item_table["obj_id"] == obj_id].object_type.iloc[0]

        raise NotImplementedError("Not implemented!")


objects_info = ObjectsInfo()
