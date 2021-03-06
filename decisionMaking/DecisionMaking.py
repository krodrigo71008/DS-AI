from typing import List

from decisionMaking.ActionRequester import ActionRequester
from decisionMaking.BehaviorTree import DSBehaviorTree
from decisionMaking.constants import MONSTER_DANGER_DISTANCE, PICK_UP_DISTANCE
from modeling.Modeling import Modeling
from modeling.objects.ObjectModel import ObjectModel
from modeling.ObjectsInfo import objects_info
from utility.Point2d import Point2d

import numpy as np


class DecisionMaking:
    def __init__(self, debug=False):
        self.primary_action = None
        self.secondary_action = None
        self.action_requester = ActionRequester()
        self.behavior_tree = DSBehaviorTree()
        self.debug = debug
        if self.debug:
            self.records = []

    # decides the action (high level)
    # should be called every loop
    def primary_system(self, modeling: Modeling):
        self.behavior_tree.update(modeling, self.action_requester)
        self.primary_action = self.action_requester.get_action()

    # decides minor steps for the primary system action
    def secondary_system(self, modeling: Modeling):
        if self.primary_action[0] == "gather":
            items = self.primary_action[1].copy()
            world = modeling.world_model
            if "food" in items:
                items.remove("food")
                items.extend(["BerryBush", "Honey", "Carrot"])
            if "CutGrass" in items:
                items.append("Grass")
            if "Twigs" in items:
                items.append("Sapling")
            obj_lists = world.get_all_of(items)
            all_objects = []
            for obj_name, obj_list in obj_lists.items():
                all_objects = [*all_objects, *obj_list]
            locations = [obj.position for obj in all_objects]
            if len(locations) == 0:
                self.secondary_action = ("explore", modeling.world_model)
            else:
                self.choose_destination(locations, modeling.world_model.player.position, all_objects)
        elif self.primary_action[0] == "craft":
            self.secondary_action = ("craft", self.primary_action[1])

    # takes control when needed
    def emergency_system(self, modeling: Modeling):
        if modeling.player_model.hunger < 30:
            foods = ["Seeds", "MonsterMeat", "Honey", "FrogLegs", "Meat"]
            food_counts = modeling.player_model.inventory.get_inventory_count(foods)
            # if we have no food, look for it
            if np.array(food_counts).sum() == 0:
                self.primary_action = ("gather", "food")
                self.secondary_system(modeling)
            else:
                if modeling.player_model.hunger < 15:
                    hunger_points_to_fill = modeling.player_model.max_hunger - modeling.player_model.hunger
                    self.decide_what_to_eat(foods, food_counts, hunger_points_to_fill)
        elif modeling.clock.day_section() == "Night":
            torch_count = modeling.player_model.inventory.get_inventory_count(["Torch"])
            if np.array(torch_count).sum() == 0:
                self.secondary_action = ("craft", ["Torch"])
            else:
                if type(modeling.player_model.inventory.hand.object).__name__ != "Torch":
                    self.secondary_action = ("equip", "Torch")
        else:
            monsters = [
                "Treeguard", "KillerBee", "Frog", "Hound", "IceHound", "FireHound", "Spider", "SpiderWarrior",
                "Tallbird", "Ghost", "GuardianPig", "Merm", "Tentacle", "ClockRook", "ClockKnight", "ClockBishop",
                "Nightmare1", "Nightmare2", "Werepig", "Mosquito"
            ]
            monster_lists = modeling.world_model.get_all_of(monsters)
            all_objects = []
            for monster_name, monster_list in monster_lists.items():
                all_objects = [*all_objects, *monster_list]
            locations = [obj.position for obj in all_objects]
            distances = [location.distance(modeling.player_model.position) for location in locations]
            if len(distances) > 0:
                closest_index = min(range(len(distances)), key=distances.__getitem__)
                if distances[closest_index] < MONSTER_DANGER_DISTANCE:
                    self.run_away_from(locations[closest_index], modeling.player_model.position)

    # helps with inventory management
    def inventory_management_system(self, modeling: Modeling):
        pass

    def choose_destination(self, objectives: List[Point2d], player_position: Point2d,
                           all_objects: List[ObjectModel]) -> None:
        closest = None
        closest_distance = None
        closest_index = None
        for index, obj_pos in enumerate(objectives):
            if closest is None or closest_distance > obj_pos.distance(player_position):
                closest = obj_pos
                closest_distance = obj_pos.distance(player_position)
                closest_index = index
        if closest_distance < PICK_UP_DISTANCE:
            self.secondary_action = ("pick_up_item", all_objects[closest_index])
        else:
            self.secondary_action = ("go_to", closest)

    def decide_what_to_eat(self, foods: List[str], food_counts: List[int], hunger_points_to_fill: float) -> None:
        # this will definitely be changed later
        best_food_and_count = (None, None)
        for pair in zip(foods, food_counts):
            food_name, count = pair
            food_info = objects_info.get_item_info(info="food_stats", name=food_name)
            health_value = food_info[0]
            hunger_value = food_info[1]
            count_to_fill = hunger_points_to_fill//hunger_value
            effective_count = min(count_to_fill, count)
            health_delta = effective_count*health_value
            if best_food_and_count[1] is None or health_delta > best_food_and_count[1]:
                best_food_and_count = ((food_name, effective_count), health_delta)
        self.secondary_action = ("eat", best_food_and_count[0])

    def run_away_from(self, danger_position: Point2d, player_position: Point2d):
        # direction_to_run in radians
        direction_to_run = (player_position - danger_position).angle()
        self.secondary_action = ("run", direction_to_run)

    # main function that should be called
    def decide(self, modeling):
        self.primary_system(modeling)
        self.secondary_system(modeling)
        self.inventory_management_system(modeling)
        self.emergency_system(modeling)
        if self.debug:
            self.records.append((self.primary_action, self.secondary_action))
