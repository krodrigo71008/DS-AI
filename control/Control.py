import math
from math import sqrt, pi

from control.constants import FIRST_INVENTORY_POSITION, INVENTORY_SPACING, HAND_INVENTORY_POSITION, KEYPRESS_DURATION, MOUSE_CLICK_DURATION, CRAFT_KEYPRESS_DURATION
from control.constants import PICK_UP_DURATION, PICK_UP_STOP_DURATION, PICK_UP_HOVER_DURATION, RUN_DURATION, FINISH_CRAFTING_DURATION, EXPLORE_DURATION
from decisionMaking.DecisionMaking import DecisionMaking
from decisionMaking.constants import PICK_UP_DISTANCE, CLOSE_ENOUGH_DISTANCE
from modeling.Modeling import Modeling
from modeling.objects.ObjectModel import ObjectModel
from modeling.ObjectsInfo import objects_info
from modeling.constants import CAMERA_HEADING, PLAYER_BASE_SPEED, CHUNK_SIZE
from utility.Point2d import Point2d
from utility.Clock import Clock
from utility.utility import clamp2pi


class Control:
    def __init__(self, debug=False, queue=None, clock=Clock()):
        self.key_action = None
        self.mouse_action = None
        self.clock : Clock = clock
        # whether the crafting menu is open
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
        # inverse indexing for the crafting tree
        self.name_to_craft_position = {}
        for key, value in self.crafting_tree_1.items():
            for index, name in enumerate(value):
                self.name_to_craft_position[name] = (key, index)
        # list of items we should craft
        self.items_to_craft = []
        # for each crafting tab, in which position we are now
        self.crafting_tabs_states = [0, 0, 0, 0, 0, 0]
        # whether we are in the middle of an action
        self.action_in_progress = False
        # start time for the current action
        self.start_time = None
        # which update should be done at the end of the current action
        self.update_at_end = None
        # current action
        self.current_action = None
        # if this is true, we should not do current action (useful for crafting for now)
        self.action_on_cooldown = False
        # whether the debug part of this class should run
        self.debug : bool = debug
        # there are some actions with multiple steps, so this indicates whether an action was finished
        self.just_finished_action = False
        # aux variable to help the picking up action
        self.pick_up_state : str = None
        # aux variable for the walking to objective phase in the picking up action
        self.estimated_time_for_objective = None
        # aux variable for the go_towards or go_precisely_towards action
        self.objective = None
        if self.debug:
            self.records = []
            self.queue = queue

    def control(self, decision_making: DecisionMaking, modeling: Modeling):
        self.clock.update()
        # secondary_action is (action, payload)
        secondary_action = decision_making.secondary_action
        should_continue = True
        if self.action_in_progress:
            # if this returns False, we should interrupt this iteration
            if not self.continue_action(modeling):
                should_continue = False
        if should_continue:
            self.action_on_cooldown = False
            self.estimated_time_for_objective = None
            self.objective = None
            self.just_finished_action = False
            # if the crafting tab is open and we don't want to craft anything right now, we should close it before anything else
            if secondary_action[0] != "craft" and self.crafting_open:
                self.key_action = (["caps_lock"], "press_and_release")
                self.mouse_action = None
                self.current_action = "close_inventory"
                self.crafting_open = False
                self.action_in_progress = True
                self.start_time = self.clock.time()
            else:
                if secondary_action[0] == "eat":
                    # this is a one step action
                    self.eat(secondary_action[1], modeling)
                    self.current_action = secondary_action[0]
                    self.action_in_progress = True
                    self.start_time = self.clock.time()
                elif secondary_action[0] == "craft":
                    # this is a multiple step action
                    # one step is one key press
                    self.craft(secondary_action[1])
                    self.current_action = secondary_action[0]
                    self.action_in_progress = True
                    self.start_time = self.clock.time()
                elif secondary_action[0] == "go_to":
                    # this is a multiple step process
                    # one step is walking for a bit
                    self.go_towards(secondary_action[1], modeling)
                    self.current_action = secondary_action[0]
                    self.action_in_progress = True
                    self.start_time = self.clock.time()
                elif secondary_action[0] == "go_precisely_to":
                    # this is a multiple step process
                    # one step is walking for a bit
                    self.go_precisely_towards(secondary_action[1], modeling)
                    self.current_action = secondary_action[0]
                    self.action_in_progress = True
                    self.start_time = self.clock.time()
                elif secondary_action[0] == "run":
                    # this is a multiple step process
                    # one step is walking for a bit
                    self.run(secondary_action[1])
                    self.current_action = secondary_action[0]
                    self.action_in_progress = True
                    self.start_time = self.clock.time()
                elif secondary_action[0] == "explore":
                    # this is a multiple step process
                    # one step is walking for a bit
                    self.explore(modeling)
                    self.current_action = secondary_action[0]
                    self.action_in_progress = True
                    self.start_time = self.clock.time()
                elif secondary_action[0] == "pick_up_item":
                    # this is a multiple step process
                    # steps are: waiting, hovering, clicking
                    self.pick_up(secondary_action[1], modeling)
                    self.current_action = secondary_action[0]
                    self.action_in_progress = True
                    self.start_time = self.clock.time()
                elif secondary_action[0] == "equip":
                    # this is a one step process
                    self.equip(secondary_action[1], modeling)
                    self.current_action = secondary_action[0]
                    self.action_in_progress = True
                    self.start_time = self.clock.time()
                elif secondary_action[0] == "unequip":
                    # this is a one step process
                    self.unequip(secondary_action[1])
                    self.current_action = secondary_action[0]
                    self.action_in_progress = True
                    self.start_time = self.clock.time()
                else:
                    raise ValueError("Invalid secondary action!")
            self.records.append(("normal_path", self.key_action, self.mouse_action, self.action_on_cooldown, 
                                 self.current_action, self.clock.time_in_seconds, self.update_at_end))
        if self.debug:
            if self.queue is not None:
                if self.current_action == "go_to" or self.current_action == "explore":
                    self.queue.put(("current_action", (self.current_action, self.objective)))
                else:
                    self.queue.put(("current_action", self.current_action))
                self.queue.put(("key_action", self.key_action))
                self.queue.put(("mouse_action", self.mouse_action))

    def continue_action(self, modeling: Modeling) -> bool:
        """Continues an ongoing action and returns whether the rest of the control should run this iteration

        :param modeling: Modeling instance
        :type modeling: Modeling
        :return: True if the rest of control should run, False if it should be interrupted
        :rtype: bool
        """
        if self.current_action == "eat":
            if self.clock.time() - self.start_time >= MOUSE_CLICK_DURATION:
                self.action_in_progress = False
        elif self.current_action == "craft":
            self.action_on_cooldown = True
            # if update_at_end is "craft", it is the final phase, after pressing enter 
            if self.update_at_end is not None and self.update_at_end[0] == "craft":
                if self.clock.time() - self.start_time >= FINISH_CRAFTING_DURATION:
                    self.action_in_progress = False
            else:
                if self.clock.time() - self.start_time >= CRAFT_KEYPRESS_DURATION:
                    self.action_in_progress = False
        elif self.current_action == "go_to":
            if self.clock.time() - self.start_time >= RUN_DURATION:
                self.action_in_progress = False
        elif self.current_action == "go_precisely_to":
            if self.clock.time() - self.start_time >= RUN_DURATION:
                self.action_in_progress = False
        elif self.current_action == "run":
            if self.clock.time() - self.start_time >= RUN_DURATION:
                self.action_in_progress = False
        elif self.current_action == "explore":
            if self.clock.time() - self.start_time >= EXPLORE_DURATION:
                self.action_in_progress = False
        elif self.current_action == "pick_up_item":
            # in this case, we're waiting a bit before hovering
            if self.pick_up_state is None:
                if self.clock.time() - self.start_time >= PICK_UP_STOP_DURATION:
                    self.action_in_progress = False
            # hovering over the object
            elif self.pick_up_state == "hover":
                if self.clock.time() - self.start_time >= PICK_UP_HOVER_DURATION:
                    self.action_in_progress = False
            # clicking and waiting until the action is finished
            elif self.pick_up_state == "click":
                self.action_on_cooldown = True
                # in this case, estimated_time_for_objective is the estimated time to get to the object, after which the player will be still
                if self.clock.time() - self.start_time >= self.estimated_time_for_objective:
                    modeling.player_model.set_direction(None)
                if self.clock.time() - self.start_time >= PICK_UP_DURATION:
                    self.action_in_progress = False
        elif self.current_action == "equip":
            if self.clock.time() - self.start_time >= MOUSE_CLICK_DURATION:
                self.action_in_progress = False
        elif self.current_action == "unequip":
            if self.clock.time() - self.start_time >= MOUSE_CLICK_DURATION:
                self.action_in_progress = False
        elif self.current_action == "close_inventory":
            self.action_on_cooldown = True
            if self.clock.time() - self.start_time >= CRAFT_KEYPRESS_DURATION:
                self.action_in_progress = False

        # each action has different signals for stopping, this will probably be changed someday
        # if self.key_action is not None:
        #     if self.key_action[1] == "press_and_release":
        #         self.action_on_cooldown = True
        #     if time.time() - self.start_time >= KEYPRESS_DURATION:
        #         self.action_in_progress = False
        # if self.mouse_action is not None:
        #     if time.time() - self.start_time >= MOUSE_CLICK_DURATION:
        #         self.action_in_progress = False
        
        if self.action_in_progress == False and self.update_at_end is not None:
            return_value = None
            if self.update_at_end[0] == "pick_up":
                # update_at_end[1] is the Modeling Object
                obj_name = type(self.update_at_end[1]).__name__
                # update the inventory depending on the collected object
                if obj_name == "BerryBush":
                    modeling.player_model.inventory.add_item("Berries", 1)
                    self.update_at_end[1].harvest()
                elif obj_name == "Grass":
                    modeling.player_model.inventory.add_item("CutGrass", 1)
                    self.update_at_end[1].harvest()
                elif obj_name == "Sapling":
                    modeling.player_model.inventory.add_item("Twigs", 1)
                    self.update_at_end[1].harvest()
                else:
                    modeling.player_model.inventory.add_item(obj_name, 1)
                return_value = False
                self.pick_up_state = None
                self.just_finished_action = True
            elif self.update_at_end[0] == "eat":
                # update player stats depending on what we ate
                food_stats = objects_info.get_item_info(info="food_stats", name=self.update_at_end[1])
                modeling.player_model.health += food_stats[0]
                modeling.player_model.hunger += food_stats[1]
                modeling.player_model.sanity += food_stats[2]
                return_value = False
                self.just_finished_action = True
            elif self.update_at_end[0] == "equip":
                # update inventory accordingly
                modeling.player_model.inventory.equip_item(self.update_at_end[1])
                return_value = False
                self.just_finished_action = True
            elif self.update_at_end[0] == "unequip":
                # update inventory accordingly
                modeling.player_model.inventory.unequip_slot(self.update_at_end[1])
                return_value = False
                self.just_finished_action = True
            elif self.update_at_end[0] == "craft":
                # update inventory accordingly
                modeling.player_model.inventory.craft(self.update_at_end[1])
                return_value = False
                self.just_finished_action = True
            elif self.update_at_end[0] == "change_pick_up_state":
                # change the internal pick up state
                change = self.update_at_end[1]
                self.pick_up_state = change
                return_value = True
            elif self.update_at_end[0] == "change_inv_state":
                # change the internal inventory state
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
                # reset player model direction
                modeling.player_model.set_direction(None)
                return_value = True
                self.just_finished_action = True
            self.update_at_end = None
            return return_value
        if self.debug:
            self.records.append(("continue_path", self.key_action, self.mouse_action, self.action_on_cooldown, 
                                 self.current_action, self.clock.time_in_seconds, self.update_at_end))
        return False

    def eat(self, food_name: str, modeling: Modeling):
        # calculate where I should click
        inv = modeling.player_model.inventory
        slots_1 = [slot_num for slot_num in inv.get_inventory_slots()]
        slots_2 = [slot.object.name if slot.object is not None else None for slot in inv.get_inventory_slots().values()]
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
        # calculate where I should click
        inv = modeling.player_model.inventory
        slot_index = inv.find_first_slot(equip_name)
        INV_SLOT_1_POS = Point2d(FIRST_INVENTORY_POSITION[0], FIRST_INVENTORY_POSITION[1])
        INV_SLOT_DELTA = Point2d(INVENTORY_SPACING[0], INVENTORY_SPACING[1])
        self.mouse_action = ("right_click", INV_SLOT_1_POS+INV_SLOT_DELTA*slot_index)
        self.key_action = None
        self.update_at_end = ("equip", equip_name)
        
    def unequip(self, equip_slot: str):
        slot_name_to_number = {
            "Hand": 0,
            "Body": 1,
            "Head": 2,
        }
        INV_SLOT_HAND_POS = Point2d(HAND_INVENTORY_POSITION[0], HAND_INVENTORY_POSITION[1])
        INV_SLOT_DELTA = Point2d(INVENTORY_SPACING[0], INVENTORY_SPACING[1])
        self.mouse_action = ("right_click", INV_SLOT_HAND_POS+INV_SLOT_DELTA*slot_name_to_number[equip_slot])
        self.key_action = None
        self.update_at_end = ("unequip", equip_slot)

    def craft(self, things_to_craft: list[str]):
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
        self.objective = objective
        player_position = modeling.player_model.position
        # PICK_UP_DISTANCE means that we should click it with mouse
        if objective.distance(player_position) < PICK_UP_DISTANCE:
            self.key_action = None
            self.mouse_action = None
            return
        # direction_to_move is in radians
        direction_to_move = (objective - player_position).angle()
        modeling.player_model.set_direction(round(direction_to_move/(pi/4))*pi/4)
        keys = self.global_direction_to_key_commands(direction_to_move)
        self.key_action = (keys, "press")
        self.mouse_action = None
        self.update_at_end = ("reset_player_direction",)

    def go_precisely_towards(self, objective: Point2d, modeling: Modeling):
        self.objective = objective
        player_position = modeling.player_model.position
        if objective.distance(player_position) < CLOSE_ENOUGH_DISTANCE:
            self.key_action = None
            self.mouse_action = None
            return
        # direction_to_move is in radians
        direction_to_move = (objective - player_position).angle()
        modeling.player_model.set_direction(round(direction_to_move/(pi/4))*pi/4)
        keys = self.global_direction_to_key_commands(direction_to_move)
        self.key_action = (keys, "press")
        self.mouse_action = None
        self.update_at_end = ("reset_player_direction",)

    def run(self, direction_to_run : float):
        keys = self.global_direction_to_key_commands(direction_to_run)
        self.key_action = (keys, "press")
        self.mouse_action = None
        self.update_at_end = ("reset_player_direction",)

    @staticmethod
    def global_direction_to_key_commands(global_direction : float) -> list[str]:
        # correcting to account for camera heading
        direction_to_move_from_camera = clamp2pi(global_direction - CAMERA_HEADING*math.pi/180)
        # discretized_direction between -4 and 4, 0 aligned with camera direction and increasing counterclockwise
        discretized_direction = round(direction_to_move_from_camera/(pi/4))
        if discretized_direction == -4:
            # up
            keys = ["w"]
        elif discretized_direction == -3:
            # up_left
            keys = ["w", "a"]
        elif discretized_direction == -2:
            # left
            keys = ["a"]
        elif discretized_direction == -1:
            # down_left
            keys = ["s", "a"]
        elif discretized_direction == 0:
            # down
            keys = ["s"]
        elif discretized_direction == 1:
            # down_right
            keys = ["s", "d"]
        elif discretized_direction == 2:
            # right
            keys = ["d"]
        elif discretized_direction == 3:
            # up_right
            keys = ["w", "d"]
        elif discretized_direction == 4:
            # up
            keys = ["w"]
        else:
            # this should never happen
            raise Exception("Invalid discretized direction!")
        return keys


    def explore(self, modeling : Modeling):
        # reminder to somehow check that I'm not stuck somewhere
        chunk = modeling.world_model.get_closest_unexplored_chunk()
        # objective is the central point of the chunk
        objective = Point2d(chunk[0]*CHUNK_SIZE + CHUNK_SIZE/2, chunk[1]*CHUNK_SIZE + CHUNK_SIZE/2)
        self.go_towards(objective, modeling)

    def pick_up(self, obj : ObjectModel, modeling : Modeling):
        if self.pick_up_state is None:
            self.key_action = None
            self.mouse_action = None
            self.update_at_end = ("change_pick_up_state", "hover")
        elif self.pick_up_state == "hover":
            bbox = obj.latest_screen_position
            self.key_action = None
            self.mouse_action = ("move", Point2d(bbox[0] + bbox[2]//2, bbox[1] + bbox[3]//2))
            self.update_at_end = ("change_pick_up_state", "click")
            # send notice that we're hovering over obj
            modeling.world_model.set_hovering_over(obj)
        elif self.pick_up_state == "click":
            bbox = obj.latest_screen_position
            self.key_action = None
            self.mouse_action = ("click", Point2d(bbox[0] + bbox[2]//2, bbox[1] + bbox[3]//2))
            player_pos = modeling.player_model.position
            distance_to_object : Point2d = obj.position - player_pos
            modeling.player_model.set_direction(distance_to_object.angle())
            self.update_at_end = ("pick_up", obj)
            # this is the estimated time that we'll take to get to obj
            self.estimated_time_for_objective = distance_to_object.distance(Point2d(0, 0))/PLAYER_BASE_SPEED  
            # send notice that we're no longer hovering over obj
            modeling.world_model.set_hovering_over(None)          
