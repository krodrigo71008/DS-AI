import math
from math import pi
import time

from control.constants import FIRST_INVENTORY_POSITION, INVENTORY_SPACING, HAND_INVENTORY_POSITION, KEYPRESS_DURATION, MOUSE_CLICK_DURATION, CRAFT_KEYPRESS_DURATION
from control.constants import PICK_UP_DURATION, PICK_UP_STOP_DURATION, PICK_UP_HOVER_DURATION, RUN_DURATION, FINISH_CRAFTING_DURATION, EXPLORE_DURATION
from control.constants import STOP_DURATION
from control.constants import PICK_UP_DISTANCE, CLOSE_ENOUGH_DISTANCE
from decisionMaking.BehaviorTrees import OceanExplorationBehaviorTree, CraftBehaviorTree, CollectSomethingBehaviorTree, ExecutionStatus
from decisionMaking.DecisionMaking import DecisionMaking, ActionRequester
from modeling.Modeling import Modeling
from modeling.objects.ObjectModel import ObjectModel
from modeling.ObjectsInfo import objects_info
from modeling.constants import CAMERA_HEADING, PLAYER_BASE_SPEED, CHUNK_SIZE
from utility.Point2d import Point2d
from utility.Clock import Clock
from utility.utility import clamp2pi


class Control:
    def __init__(self, debug=False, clock=Clock()):
        self.key_action = None
        self.mouse_action = None
        self.clock : Clock = clock
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

        self.action_requester = ActionRequester()
        self.ocean_exploration_behavior_tree = OceanExplorationBehaviorTree()
        self.crafting_behavior_tree = CraftBehaviorTree()
        self.collect_something_tree = None # this gets created when we need it

        # which update should be done at the end of the current action
        self.update_at_end = None
        # current action
        self.current_action = None
        self.current_payload = None
        # whether the debug part of this class should run
        self.debug : bool = debug
        # aux variable for the go_towards or go_towards action
        self.objective = None
        if self.debug:
            self.records = []

    def control(self, decision_making: DecisionMaking, modeling: Modeling):
        self.clock.update()
        # primary_action is (action, payload)
        primary_action = decision_making.primary_action
        resources_request = decision_making.resources_request
        if resources_request is not None and primary_action[0] in ["nothing", "explore", "run"]:
            self.gather(modeling, resources_request)
        else:
            if len(primary_action) == 1:
                self.end_action_and_call(primary_action[0], modeling, None)
            else:
                self.end_action_and_call(primary_action[0], modeling, primary_action[1])

        action = self.action_requester.get_action()
        
        if action is None or action[0] == "nothing":
            self.key_action = None
            self.mouse_action = None
            return (action, self.key_action, self.mouse_action)
        if action[0] == "go":
            self.go_towards(action[1], modeling)
        elif action[0] == "press_and_release":
            self.key_action = (action[1], "press_and_release")
            self.mouse_action = None
        elif action[0] == "run":
            keys = self.global_direction_to_key_commands(action[1])
            self.key_action = (keys, "press")
            self.mouse_action = None
        elif action[0] == "eat":
            # calculate where I should click
            inv = modeling.player_model.inventory
            slots_1 = [slot_num for slot_num in inv.get_inventory_slots()]
            slots_2 = [slot.object.name if slot.object is not None else None for slot in inv.get_inventory_slots().values()]
            for elem in zip(slots_1, slots_2):
                # elem is (slot_number, slot_object_name)
                if elem[1] is not None and elem[1] == action[1]:
                    INV_SLOT_1_POS = Point2d(FIRST_INVENTORY_POSITION[0], FIRST_INVENTORY_POSITION[1])
                    INV_SLOT_DELTA = Point2d(INVENTORY_SPACING[0], INVENTORY_SPACING[1])
                    self.mouse_action = ("right_click", INV_SLOT_1_POS+INV_SLOT_DELTA*elem[0])
                    self.key_action = None
                    break
            food_stats = objects_info.get_item_info(info="food_stats", name=action[1])
            modeling.player_model.health += food_stats[0]
            modeling.player_model.hunger += food_stats[1]
            modeling.player_model.sanity += food_stats[2]
        elif action[0] == "equip":
            # calculate where I should click
            inv = modeling.player_model.inventory
            slot_index = inv.find_first_slot(action[1])
            INV_SLOT_1_POS = Point2d(FIRST_INVENTORY_POSITION[0], FIRST_INVENTORY_POSITION[1])
            INV_SLOT_DELTA = Point2d(INVENTORY_SPACING[0], INVENTORY_SPACING[1])
            self.mouse_action = ("right_click", INV_SLOT_1_POS+INV_SLOT_DELTA*slot_index)
            self.key_action = None
            modeling.player_model.inventory.equip_item(action[1])
        elif action[0] == "unequip":
            slot_name_to_number = {
                "Hand": 0,
                "Body": 1,
                "Head": 2,
            }
            INV_SLOT_HAND_POS = Point2d(HAND_INVENTORY_POSITION[0], HAND_INVENTORY_POSITION[1])
            INV_SLOT_DELTA = Point2d(INVENTORY_SPACING[0], INVENTORY_SPACING[1])
            self.mouse_action = ("right_click", INV_SLOT_HAND_POS+INV_SLOT_DELTA*slot_name_to_number[action[1]])
            self.key_action = None
            modeling.player_model.inventory.unequip_slot(action[1])
        elif action[0] == "close_crafting_menu":
            self.key_action = ("caps_lock", "press_and_release")
            self.mouse_action = None
            modeling.crafting_model.crafting_open = False

        self.action_requester.set_action(None)

        if self.debug:
            return (action, self.key_action, self.mouse_action)

    def end_action_and_call(self, function_ : str, modeling : Modeling, payload):
        if self.current_action is not None and self.current_action != function_:
            if self.current_action == "nothing":
                pass
            elif self.current_action == "gather":
                if self.collect_something_tree is not None:
                    running_leaf = self.collect_something_tree.get_running_leaf()
                    if running_leaf is not None and running_leaf == "CollectSomething":
                        # if we are collecting something, we need to finish collecting it
                        self.gather(modeling, *self.current_payload)
                        return
            # we can always interrupt exploring with no consequences
            elif self.current_action == "explore":
                pass
            elif self.current_action == "craft":
                self.action_requester.set_action(("close_crafting_menu",))
                self.current_action = "nothing"
                return
            elif self.current_action == "run":
                pass
            elif self.current_action == "equip":
                pass
            elif self.current_action == "eat":
                pass

        if function_ == "nothing":
            self.do_nothing()
        elif function_ == "gather":
            self.gather(modeling, payload)
        elif function_ == "explore":
            self.explore(modeling, "ocean", payload)
        elif function_ == "craft":
            self.craft(modeling, payload)
        elif function_ == "run":
            self.run(modeling, payload)
        elif function_ == "equip":
            self.equip(payload)
        elif function_ == "eat":
            self.eat(payload)

    @staticmethod
    def get_closest_point(point_list: list[Point2d], player_position: Point2d):
        closest_distance = None
        closest_point = None
        for point in point_list:
            dist = point.distance(player_position)
            if closest_distance is None or dist < closest_distance:
                closest_distance = dist
                closest_point = point
        
        return closest_point

    def eat(self, food_name: str):
        self.action_requester.set_action(("eat", food_name))
        self.current_action = "eat"
        self.current_payload = (food_name,)

    def equip(self, equip_name: str):
        self.action_requester.set_action(("equip", equip_name))
        self.current_action = "equip"
        self.current_payload = (equip_name,)
        
    def gather(self, modeling: Modeling, item_list : list[tuple[str, int]]) -> None:
        """Gather items

        :param modeling: modeling
        :type modeling: Modeling
        :param item_list: list with names of items to gather and their amount
        :type item_list: list[tuple[str, int]]
        """
        if self.collect_something_tree is None:
            items = []
            for name, amount in item_list:
                if name == "food":
                    items.extend([("Berries", amount), ("Carrot", amount)])
                else:
                    items.append((name, amount))
            
            wanted_items = []
            missing_resources = modeling.player_model.inventory.check_missing_resources_by_name(items)
            for name, amount in missing_resources:
                if amount > 0:
                    wanted_items.append(name)

            if len(wanted_items) == 0:
                # this means all requests are satisfied
                self.key_action = None
                self.mouse_action = None
                return

            sources = []
            for item in wanted_items:
                sources.extend(objects_info.get_item_info("sources", name=item))
            
            sources.extend(wanted_items)

            obj_lists = modeling.world_model.get_all_of(sources)
            all_positions = []
            for list_ in obj_lists.values():
                all_positions.extend([obj.position() for obj in list_])
            if len(all_positions) == 0:
                self.explore(modeling, "resources", items)
                return
            else:
                closest_object = self.get_closest_point(all_positions, modeling.player_position())
                self.collect_something_tree = CollectSomethingBehaviorTree(closest_object)
                modeling.world_model.set_pickup_object(closest_object)
            
        
        if self.collect_something_tree.update(modeling, self.action_requester) == ExecutionStatus.SUCCESS:
            if self.collect_something_tree.objective.yield_ is not None:
                modeling.player_model.inventory.add_item(self.collect_something_tree.objective.yield_, 1)
                modeling.world_model.handle_object_harvested(self.collect_something_tree.objective)
            self.collect_something_tree = None
            modeling.world_model.set_pickup_object(None)
        
        self.current_action = "gather"
        self.current_payload = (item_list,)

    def unequip(self, equip_slot: str):
        self.action_requester.set_action(("unqeuip", equip_slot))

    def craft(self, modeling: Modeling, item: str):
        if modeling.player_model.inventory.can_craft(item):
            modeling.crafting_model.next_craft = item
            if self.crafting_behavior_tree.update(modeling, self.action_requester):
                modeling.player_model.inventory.craft(modeling.crafting_model.next_craft)
        else:
            materials = objects_info.calculate_raw_resources([(item, 1)], info="name")
            self.gather(modeling, materials, "main")
            return
        
        self.current_action = "craft"
        self.current_payload = (item,)

    def go_towards(self, objective: Point2d, modeling: Modeling):
        self.objective = objective
        player_position = modeling.player_position()
        # direction_to_move is in radians
        direction_to_move = (objective - player_position).angle()
        modeling.set_direction(round(direction_to_move/(pi/4))*pi/4)
        keys = self.global_direction_to_key_commands(direction_to_move)
        self.key_action = (keys, "press")
        self.mouse_action = None

    def run(self, modeling : Modeling, direction_to_run : float):
        modeling.set_direction(direction_to_run)
        self.action_requester.set_action(("run", direction_to_run))
        self.current_action = "run"
        self.current_payload = (direction_to_run,)

    @staticmethod
    def global_direction_to_key_commands(global_direction : float) -> list[str]:
        # correcting to account for camera heading
        direction_to_move_from_camera = clamp2pi(global_direction - CAMERA_HEADING*pi/180)
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

    def do_nothing(self):
        self.action_requester.set_action(("nothing",))
        self.current_action = "nothing"

    def explore(self, modeling : Modeling, type_ : str, resources : list = []):
        if type_ == "ocean":
            self.ocean_exploration_behavior_tree.update(modeling, self.action_requester)
        elif type_ == "resources":
            candidate_points_to_explore = []
            for resource in resources:
                # I could have some sort of logic in here to find out where I should explore for certain resources
                chunk = modeling.world_model.get_closest_unexplored_chunk()
                # objective is the central point of the chunk
                objective = Point2d(chunk[0]*CHUNK_SIZE + CHUNK_SIZE/2, chunk[1]*CHUNK_SIZE + CHUNK_SIZE/2)
                candidate_points_to_explore.append(objective)

            closest_object = self.get_closest_point(candidate_points_to_explore, modeling.player_position())

            self.action_requester.set_action(("go", closest_object))
        
        self.current_action = "explore"
        self.current_payload = (type_, resources)


class ControlTimer(Control):
    def __init__(self, debug=False, clock=Clock()):
        super().__init__(debug, clock)
        self.time_records_list = []

    def continue_action(self, modeling: Modeling) -> bool:
        t1 = time.time_ns()
        return_value = super().continue_action(modeling)
        t2  = time.time_ns()
        self.time_records_list.append(("continue_action", t2-t1))
        return return_value

    def eat(self, food_name: str, modeling: Modeling):
        t1 = time.time_ns()
        super().eat(food_name, modeling)
        t2  = time.time_ns()
        self.time_records_list.append(("eat", t2-t1))
    
    def equip(self, equip_name: str, modeling: Modeling):
        t1 = time.time_ns()
        super().equip(equip_name, modeling)
        t2  = time.time_ns()
        self.time_records_list.append(("equip", t2-t1))
    
    def unequip(self, equip_slot: str):
        t1 = time.time_ns()
        super().unequip(equip_slot)
        t2  = time.time_ns()
        self.time_records_list.append(("unequip", t2-t1))
    
    def craft(self, things_to_craft: list[str]):
        t1 = time.time_ns()
        super().craft(things_to_craft)
        t2  = time.time_ns()
        self.time_records_list.append(("craft", t2-t1))
    
    def go_towards(self, objective: Point2d, modeling: Modeling):
        t1 = time.time_ns()
        super().go_towards(objective, modeling)
        t2  = time.time_ns()
        self.time_records_list.append(("go_towards", t2-t1))
    
    def run(self, direction_to_run: float, modeling: Modeling):
        t1 = time.time_ns()
        super().run(direction_to_run, modeling)
        t2  = time.time_ns()
        self.time_records_list.append(("run", t2-t1))
    
    def explore(self, modeling: Modeling):
        t1 = time.time_ns()
        super().explore(modeling)
        t2  = time.time_ns()
        self.time_records_list.append(("explore", t2-t1))
    
    def pick_up(self, obj: ObjectModel, modeling: Modeling):
        t1 = time.time_ns()
        super().pick_up(obj, modeling)
        t2  = time.time_ns()
        self.time_records_list.append(("pick_up", t2-t1))
    
    def control(self, decision_making: DecisionMaking, modeling: Modeling):
        t1 = time.time_ns()
        return_value = super().control(decision_making, modeling)
        t2  = time.time_ns()
        self.time_records_list.append(("control", t2-t1))
        return return_value
