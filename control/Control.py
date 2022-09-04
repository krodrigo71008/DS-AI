import math
from random import randint
from math import sqrt, pi
from typing import List
import time

from control.constants import FIRST_INVENTORY_POSITION, INVENTORY_SPACING, KEYPRESS_DURATION, MOUSE_CLICK_DURATION
from decisionMaking.DecisionMaking import DecisionMaking
from modeling.Modeling import Modeling
from modeling.objects.ObjectModel import ObjectModel
from modeling.ObjectsInfo import objects_info
from modeling.constants import CAMERA_HEADING
from utility.Point2d import Point2d
from utility.utility import clamp2pi


class Control:
    def __init__(self, debug=False, queue=None):
        self.key_action = None
        self.mouse_action = None
        self.crafting_open = False
        self.current_crafting_tab = 0
        self.crafting_tree_1 = {
            0: ["Axe", "Pickaxe", "Shovel", "Hammer", "Pitchfork", "Razor", "FeatherPencil"],
            1: ["Campfire", "FirePit", "Torch"],
            2: ["Trap", "BirdTrap", "Compass", "Backpack", "HealingSalve", "StrawRoll", "PrettyParasol",
                "Umbrella", "Net", "FishingRod"],
            3: ["ScienceMachine", "AlchemyEngine", "ThermalMeasure", "Rainometer", "LightningRod"],
            4: ["Spear", "GrassSuit", "LogSuit", "SleepDart", "FireDart", "BlowDart", "BeeMine"],
            5: ["Garland", "RabbitEarmuffs", "StrawHat", "BeefaloHat", "TopHat"]
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
        self.action_on_cooldown = True
        self.debug = debug
        self.just_finished_action = False
        if self.debug:
            self.records = []
            self.queue = queue

    def control(self, decision_making: DecisionMaking, modeling: Modeling):
        self.just_finished_action = False
        # secondary_action is (action, payload)
        secondary_action = decision_making.secondary_action
        if self.action_in_progress:
            # if this returns False, we should interrupt this iteration
            if not self.continue_action(modeling):
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
        elif secondary_action[0] == "run":
            self.run(secondary_action[1])
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
            self.records.append((self.key_action, self.mouse_action, self.action_on_cooldown))
            if self.queue is not None:
                self.queue.put(("key_action", self.key_action))
                self.queue.put(("mouse_action", self.mouse_action))

    def continue_action(self, modeling: Modeling) -> bool:
        """Continues an ongoing action and returns whether the rest of the control should run this iteration

        :param modeling: Modeling instance
        :type modeling: Modeling
        :return: True if the rest of control should run, False if it should be interrupted
        :rtype: bool
        """
        # each action has different signals for stopping, this will probably be changed someday
        if self.key_action is not None:
            if self.key_action[1] == "press_and_release":
                self.action_on_cooldown = True
            if time.time() - self.start_time >= KEYPRESS_DURATION:
                self.action_in_progress = False
        if self.mouse_action is not None:
            if time.time() - self.start_time >= MOUSE_CLICK_DURATION:
                self.action_in_progress = False
        if self.action_in_progress == False and self.update_at_end is not None:
            return_value = None
            if self.update_at_end[0] == "pick_up":
                obj_name = type(self.update_at_end[1]).__name__
                if obj_name == "BerryBush":
                    modeling.player_model.inventory.add_item("Berry")
                elif obj_name == "Honey":
                    modeling.player_model.inventory.add_item("Honey")
                elif obj_name == "Carrot":
                    modeling.player_model.inventory.add_item("Carrot")
                return_value = False
            elif self.update_at_end[0] == "eat":
                food_stats = objects_info.get_item_info(info="food_stats", name=self.update_at_end[1])
                modeling.player_model.health += food_stats[0]
                modeling.player_model.hunger += food_stats[1]
                modeling.player_model.sanity += food_stats[2]
                return_value = False
            elif self.update_at_end[0] == "equip":
                modeling.player_model.inventory.equip_item(self.update_at_end[1])
                return_value = False
            elif self.update_at_end[0] == "craft":
                modeling.player_model.inventory.craft(self.update_at_end[1])
                return_value = False
            elif self.update_at_end[0] == "change_inv_state":
                change = self.update_at_end[1]
                if change == "up":
                    self.current_crafting_tab -= 1
                elif change == "down":
                    self.current_crafting_tab += 1
                elif change == "left":
                    self.crafting_tabs_states[self.current_crafting_tab] -= 1
                elif change == "right":
                    self.crafting_tabs_states[self.current_crafting_tab] += 1
                return_value = True
            elif self.update_at_end[0] == "reset_player_direction":
                modeling.player_model.set_direction("none")
                return_value = True
            self.update_at_end = None
            self.just_finished_action = True
            return return_value
        if self.debug:
            self.records.append((self.key_action, self.mouse_action, self.action_on_cooldown))
        return False

    def eat(self, food_name: str, modeling: Modeling):
        inv = modeling.player_model.inventory
        slots_1 = [slot_num for slot_num in inv.slots]
        slots_2 = [slot.object.name if slot.object is not None else None for slot in inv.slots.values()]
        for elem in zip(slots_1, slots_2):
            # elem is (slot_number, slot_object_name)
            if elem[1] is not None and elem[1] == food_name:
                INV_SLOT_1_POS = Point2d(FIRST_INVENTORY_POSITION[0], FIRST_INVENTORY_POSITION[1])
                INV_SLOT_DELTA = Point2d(INVENTORY_SPACING[0], INVENTORY_SPACING[1])
                self.mouse_action = ("right_click", INV_SLOT_1_POS+INV_SLOT_DELTA*elem[0])
                self.key_action = None
                self.update_at_end = ("eat", food_name)
                return

    def equip(self, equip_name: str, modeling: Modeling):
        inv = modeling.player_model.inventory
        slots_1 = [slot_num for slot_num in inv.slots]
        slots_2 = [slot.object.name if slot.object is not None else None for slot in inv.slots.values()]
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
        self.action_on_cooldown = False
        if not self.crafting_open:
            self.key_action = (["caps_lock"], "press_and_release")
            self.crafting_open = True
        else:
            # record what needs to be crafted (if needed)
            if len(self.items_to_craft) == 0:
                self.items_to_craft = things_to_craft
            for item in self.items_to_craft:
                wanted_position = self.name_to_craft_position[item]
                # wasd controls are default on crafting menu
                # updating the crafting state happens when the action is finished, not here
                if wanted_position[0] < self.current_crafting_tab:
                    self.key_action = (["w"], "press_and_release")
                    self.update_at_end = ("change_inv_state", "up")
                elif wanted_position[0] > self.current_crafting_tab:
                    self.key_action = (["s"], "press_and_release")
                    self.update_at_end = ("change_inv_state", "down")
                else:
                    if wanted_position[1] < self.crafting_tabs_states[self.current_crafting_tab]:
                        self.key_action = (["a"], "press_and_release")
                        self.update_at_end = ("change_inv_state", "left")
                    elif wanted_position[1] > self.crafting_tabs_states[self.current_crafting_tab]:
                        self.key_action = (["d"], "press_and_release")
                        self.update_at_end = ("change_inv_state", "right")
                    else:
                        self.key_action = (["enter"], "press_and_release")
                        self.update_at_end = ("craft", item)
                        self.crafting_open = False
        self.mouse_action = None

    def go_towards(self, objective: Point2d, modeling: Modeling):
        player_position = modeling.player_model.position
        # direction_to_move is in radians
        direction_to_move = (objective - player_position).angle()
        modeling.player_model.set_direction(round(direction_to_move/(pi/4)))
        keys = self.global_direction_to_key_commands(direction_to_move)
        self.key_action = (keys, "press")
        self.mouse_action = None
        self.update_at_end = ("reset_player_direction")

    def run(self, direction_to_run : float):
        keys = self.global_direction_to_key_commands(direction_to_run)
        self.key_action = (keys, "press")
        self.mouse_action = None
        self.update_at_end = ("reset_player_direction")

    @staticmethod
    def global_direction_to_key_commands(global_direction : float) -> list[str]:
        # correcting to account for camera heading
        direction_to_move_from_camera = clamp2pi(global_direction - CAMERA_HEADING*math.pi/180)
        # discretized_direction between -4 and 4, 0 aligned with camera direction and increasing clockwise
        discretized_direction = round(direction_to_move_from_camera/(pi/4))
        if discretized_direction == -4:
            # up
            keys = ["w"]
        elif discretized_direction == -3:
            # up_right
            keys = ["w", "d"]
        elif discretized_direction == -2:
            # right
            keys = ["d"]
        elif discretized_direction == -1:
            # down_right
            keys = ["s", "d"]
        elif discretized_direction == 0:
            # down
            keys = ["s"]
        elif discretized_direction == 1:
            # down_left
            keys = ["s", "a"]
        elif discretized_direction == 2:
            # left
            keys = ["a"]
        elif discretized_direction == 3:
            # up_left
            keys = ["w", "a"]
        elif discretized_direction == 4:
            # up
            keys = ["w"]
        else:
            # this should never happen
            raise Exception("Invalid discretized direction!")
        return keys


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
        self.key_action = (["space"], "press_and_release")
        self.mouse_action = None
        self.update_at_end = ("pick_up", obj)
