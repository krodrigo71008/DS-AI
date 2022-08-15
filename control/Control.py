from random import randint
from math import sqrt, pi
from typing import List
import time

from control.constants import FIRST_INVENTORY_POSITION, INVENTORY_SPACING, KEYPRESS_DURATION, MOUSE_CLICK_DURATION
from decisionMaking.DecisionMaking import DecisionMaking
from modeling.Modeling import Modeling
from modeling.objects.ObjectModel import ObjectModel
from modeling.ObjectsInfo import objects_info
from utility.Point2d import Point2d


class Control:
    def __init__(self, debug=False, queue=None):
        self.key_action = None
        self.mouse_action = None
        self.crafting_open = False
        self.current_crafting_tab = 0
        self.crafting_tree_1 = {
            0: ["axe", "pickaxe", "shovel", "hammer", "pitchfork", "razor", "feather_pencil"],
            1: ["campfire", "fire_pit", "torch"],
            2: ["trap", "bird_trap", "compass", "backpack", "healing_salve", "straw_roll", "pretty_parasol",
                "umbrella", "net", "fishing_rod"],
            3: ["science_machine", "alchemy_engine", "thermal_measure", "rainometer", "lightning_rod"],
            4: ["spear", "grass_suit", "log_suit", "sleep_dart", "fire_dart", "blow_dart", "bee_mine"],
            5: ["garland", "rabbit_earmuffs", "straw_hat", "beefalo_hat", "top_hat"]
        }
        self.name_to_craft_position = {}
        for key, value in self.crafting_tree_1.items():
            for index, name in enumerate(value):
                self.name_to_craft_position[name] = (key, index)
        self.items_to_craft = []
        self.crafting_tabs_states = [0, 0, 0, 0, 0, 0]
        self.action_in_progress = False
        self.start_time = None
        self.update_at_end = None
        self.debug = debug
        if self.debug:
            self.records = []
            self.queue = queue

    def control(self, decision_making: DecisionMaking, modeling: Modeling):
        # secondary_action is (action, payload)
        secondary_action = decision_making.secondary_action
        if self.debug:
            self.records.append((self.key_action, self.mouse_action))
        if self.action_in_progress:
            self.continue_action(modeling)
            if self.action_in_progress:
                return
        if secondary_action[0] == "eat":
            self.eat(secondary_action[1], modeling)
            self.action_in_progress = True
            self.start_time = time.time()
        elif secondary_action[0] == "craft":
            self.craft(secondary_action[1])
            self.action_in_progress = True
            self.start_time = time.time()
        elif secondary_action[0] == "go_to":
            self.go_towards(secondary_action[1], modeling)
            self.action_in_progress = True
            self.start_time = time.time()
        elif secondary_action[0] == "explore":
            self.explore(modeling)
            self.action_in_progress = True
            self.start_time = time.time()
        elif secondary_action[0] == "pick_up_item":
            self.pick_up(secondary_action[1])
            self.action_in_progress = True
            self.start_time = time.time()
        elif secondary_action[0] == "equip":
            self.equip(secondary_action[1], modeling)
            self.action_in_progress = True
            self.start_time = time.time()
        if self.debug:
            self.queue.put(("key_action", self.key_action))
            self.queue.put(("mouse_action", self.mouse_action))

    def continue_action(self, modeling: Modeling):
        # each action has different signals for stopping, this will probably be changed someday
        if self.key_action is not None:
            if time.time() - self.start_time >= KEYPRESS_DURATION:
                self.action_in_progress = False
        if self.mouse_action is not None:
            if time.time() - self.start_time >= MOUSE_CLICK_DURATION:
                self.action_in_progress = False
        if self.action_in_progress == False and self.update_at_end is not None:
            if self.update_at_end[0] == "pick_up":
                obj_name = type(self.update_at_end[1]).__name__
                if obj_name == "BerryBush":
                    modeling.player_model.inventory.add_item("Berry")
                elif obj_name == "Honey":
                    modeling.player_model.inventory.add_item("Honey")
                elif obj_name == "Carrot":
                    modeling.player_model.inventory.add_item("Carrot")
            elif self.update_at_end[0] == "eat":
                food_stats = objects_info.get_item_info(info="food_stats", name=self.update_at_end[1])
                modeling.player_model.health += food_stats[0]
                modeling.player_model.hunger += food_stats[1]
                modeling.player_model.sanity += food_stats[2]
            elif self.update_at_end[0] == "equip":
                modeling.player_model.inventory.equip_item(self.update_at_end[1])
            elif self.update_at_end[0] == "craft":
                modeling.player_model.inventory.craft(self.update_at_end[1])
            elif self.update_at_end[0] == "change_inv_state":
                change = self.update_at_end[1]
                if change == "up":
                    self.current_crafting_tab += 1
                elif change == "down":
                    self.current_crafting_tab -= 1
                elif change == "left":
                    self.crafting_tabs_states[self.current_crafting_tab] -= 1
                elif change == "right":
                    self.crafting_tabs_states[self.current_crafting_tab] += 1
            elif self.update_at_end[0] == "reset_player_direction":
                modeling.player_model.set_direction("none")
            self.update_at_end = None

    def eat(self, food_name: str, modeling: Modeling):
        inv = modeling.player_model.inventory
        slots_1 = [slot_num for slot_num in inv.slots]
        slots_2 = [slot.object.name for slot in inv.slots.values()]
        for elem in zip(slots_1, slots_2):
            # elem is (slot_number, slot_object_name)
            if elem[1] == food_name:
                INV_SLOT_1_POS = Point2d(FIRST_INVENTORY_POSITION[0], FIRST_INVENTORY_POSITION[1])
                INV_SLOT_DELTA = Point2d(INVENTORY_SPACING[0], INVENTORY_SPACING[1])
                self.mouse_action = ("right_click", INV_SLOT_1_POS+INV_SLOT_DELTA*elem[0])
                self.key_action = None
                self.update_at_end = ("eat", food_name)
                return

    def equip(self, equip_name: str, modeling: Modeling):
        inv = modeling.player_model.inventory
        slots_1 = [slot_num for slot_num in inv.slots]
        slots_2 = [slot.object.name for slot in inv.slots.values()]
        for elem in zip(slots_1, slots_2):
            # elem is (slot_number, slot_object_name)
            if elem[1] == equip_name:
                INV_SLOT_1_POS = Point2d(FIRST_INVENTORY_POSITION[0], FIRST_INVENTORY_POSITION[1])
                INV_SLOT_DELTA = Point2d(INVENTORY_SPACING[0], INVENTORY_SPACING[1])
                self.mouse_action = ("right_click", INV_SLOT_1_POS+INV_SLOT_DELTA*elem[0])
                self.key_action = None
                self.update_at_end = ("equip", equip_name)
                return

    def craft(self, things_to_craft: List[str]):
        if not self.crafting_open:
            self.key_action = ["caps_lock"]
        else:
            # record what needs to be crafted (if needed)
            if len(self.items_to_craft) == 0:
                self.items_to_craft = things_to_craft
            for item in self.items_to_craft:
                wanted_position = self.name_to_craft_position[item]
                # wasd controls are default on crafting menu
                # updating the crafting state happens when the action is finished, not here
                if wanted_position[0] < self.current_crafting_tab:
                    self.key_action = ["w"]
                    self.update_at_end = ("change_inv_state", "up")
                elif wanted_position[0] > self.current_crafting_tab:
                    self.key_action = ["s"]
                    self.update_at_end = ("change_inv_state", "down")
                else:
                    if wanted_position[1] < self.crafting_tabs_states[self.current_crafting_tab]:
                        self.key_action = ["a"]
                        self.update_at_end = ("change_inv_state", "left")
                    elif wanted_position[1] > self.crafting_tabs_states[self.current_crafting_tab]:
                        self.key_action = ["d"]
                        self.update_at_end = ("change_inv_state", "right")
                    else:
                        self.key_action = ["enter"]
                        self.update_at_end = ("craft", item)
        self.mouse_action = None

    def go_towards(self, objective: Point2d, modeling: Modeling):
        player_position = modeling.player_model.position
        # direction_to_move is in radians
        direction_to_move = (objective - player_position).angle()
        # discretized_direction between -4 and 4
        discretized_direction = round(direction_to_move/(pi/4))
        if discretized_direction == -4:
            keys = ["a"]
            modeling.player_model.set_direction("left")
        elif discretized_direction == -3:
            keys = ["a", "s"]
            modeling.player_model.set_direction("down_left")
        elif discretized_direction == -2:
            keys = ["s"]
            modeling.player_model.set_direction("down")
        elif discretized_direction == -1:
            keys = ["d", "s"]
            modeling.player_model.set_direction("down_right")
        elif discretized_direction == 0:
            keys = ["d"]
            modeling.player_model.set_direction("right")
        elif discretized_direction == 1:
            keys = ["d", "w"]
            modeling.player_model.set_direction("up_right")
        elif discretized_direction == 2:
            keys = ["w"]
            modeling.player_model.set_direction("up")
        elif discretized_direction == 3:
            keys = ["a", "w"]
            modeling.player_model.set_direction("up_left")
        elif discretized_direction == 4:
            keys = ["a"]
            modeling.player_model.set_direction("left")
        else:
            # this should never happen
            raise Exception("Invalid discretized direction!")
        self.key_action = keys
        self.mouse_action = None
        self.update_at_end = ("reset_player_direction")

    def explore(self, modeling):
        # reminder to somehow check that I'm not stuck somewhere
        direction = randint(0, 7)
        dx = [1, 1, 0, -1, -1, -1, 0, 1]
        dy = [0, -1, -1, -1, 0, 1, 1, 1]
        norm = [1, sqrt(2), 1, sqrt(2), 1, sqrt(2), 1, sqrt(2)]
        DISTANCE = 100
        objective = (modeling.world_model.player.position + Point2d(dx[direction], dy[direction])
                     * (DISTANCE/norm[direction]))
        self.go_towards(objective, modeling)

    def pick_up(self, obj: ObjectModel):
        self.key_action = ["space"]
        self.mouse_action = None
        self.update_at_end = ("pick_up", obj)
