from __future__ import annotations
from typing import TYPE_CHECKING
import math
import time

import numpy as np

from decisionMaking.ActionRequester import ActionRequester
from decisionMaking.BehaviorTrees import DSBehaviorTree
from decisionMaking.constants import MONSTER_DANGER_DISTANCE
from modeling.Modeling import Modeling
from modeling.ObjectsInfo import objects_info
if TYPE_CHECKING:
    from modeling.Modeling import Modeling
    from modeling.objects.ObjectModel import ObjectModel
    from modeling.mobs.MobModel import MobModel
    from utility.Point2d import Point2d


class DecisionMaking:
    def __init__(self, debug=False):
        self.primary_decision = None
        self.resources_request = None
        self.action_requester = ActionRequester()
        self.behavior_tree = DSBehaviorTree()
        self.is_emergency = False
        self.debug : bool = debug
        if self.debug:
            self.records = []

    # decides the action (high level)
    # should be called every loop
    def primary_system(self, modeling: Modeling) -> None:
        self.behavior_tree.update(modeling, self.action_requester)
        self.primary_decision = self.action_requester.get_action()
        self.resources_request = self.action_requester.get_resources_request()

    # takes control when needed
    def emergency_system(self, modeling: Modeling) -> None:
        # if hunger is too low
        if modeling.player_model.hunger < 30:
            self.is_emergency = True
            foods = ["Seeds", "MonsterMeat", "Honey", "FrogLegs", "Meat", "Berries", "Drumstick"]
            food_counts = modeling.player_model.inventory.get_inventory_count(foods)
            # if we have no food, look for it
            if np.array(food_counts).sum() == 0:
                self.primary_decision = ("gather", [("food", 99)])
            else:
                if modeling.player_model.hunger < 15:
                    hunger_points_to_fill = modeling.player_model.max_hunger - modeling.player_model.hunger
                    self.decide_what_to_eat(foods, food_counts, hunger_points_to_fill)
        # if it's nighttime
        elif modeling.clock.day_section() == "Night":
            self.is_emergency = True
            torch_count = modeling.player_model.inventory.get_inventory_count(["Torch"])
            # this will fail if we don't have materials to craft it, but we should have enough
            if np.array(torch_count).sum() == 0:
                self.primary_decision = ("craft", "Torch")
            else:
                if modeling.player_model.inventory.slots["Hand"].object.name != "Torch":
                    self.primary_decision = ("equip", "Torch")
        else:
            monsters = [
                "Treeguard", "KillerBee", "Frog", "Hound", "IceHound", "FireHound", "Spider", "SpiderWarrior",
                "Tallbird", "Ghost", "GuardianPig", "Merm", "Tentacle", "ClockRook", "ClockKnight", "ClockBishop",
                "Nightmare1", "Nightmare2", "Werepig", "Mosquito"
            ]
            monster_lists = modeling.world_model.get_all_of(monsters)
            all_objects : list[ObjectModel | MobModel] = []
            for monster_list in monster_lists.values():
                all_objects = [*all_objects, *monster_list]
            locations = [obj.position() for obj in all_objects]
            distances = [location.distance(modeling.player_position()) for location in locations]
            if len(distances) > 0:
                closest_index = min(range(len(distances)), key=distances.__getitem__)
                if distances[closest_index] < MONSTER_DANGER_DISTANCE:
                    self.is_emergency = True
                    self.run_away_from(locations[closest_index], modeling.player_position())

    # helps with inventory management
    def decide_how_to_free_inventory_space(self, modeling: Modeling) -> None:
        pass

    def decide_what_to_eat(self, foods: list[str], food_counts: list[int], hunger_points_to_fill: float) -> None:
        # this will definitely be changed later
        # we choose the food that would damage our health the least for now
        best_food_and_count = (None, None)
        for pair in zip(foods, food_counts):
            food_name, count = pair
            food_info = objects_info.get_item_info(info="food_stats", name=food_name)
            health_value = food_info[0]
            hunger_value = food_info[1]
            # how much we need to eat to fill our hunger enough
            count_to_fill = hunger_points_to_fill//hunger_value
            effective_count = min(count_to_fill, count)
            # how eating all this would affect my health
            health_delta = effective_count*health_value
            if best_food_and_count[1] is None or health_delta > best_food_and_count[1]:
                best_food_and_count = ((food_name, effective_count), health_delta)
        self.primary_decision = ("eat", best_food_and_count[0])

    def run_away_from(self, danger_position: Point2d, player_position: Point2d) -> None:
        # direction_to_run in radians
        direction_to_run = (player_position - danger_position).angle()
        self.primary_decision = ("run", direction_to_run)

    # main function that should be called
    def decide(self, modeling):
        self.is_emergency = False
        self.primary_system(modeling)
        self.emergency_system(modeling)
        
        if self.debug:
            self.records.append((self.primary_decision, self.resources_request))
            return (self.primary_decision, self.resources_request)

class DecisionMakingTimer(DecisionMaking):
    def __init__(self, debug=False):
        super().__init__(debug)
        self.time_records = []
        self.split_names = ["primary_system", "secondary_system", "emergency_system", "decide_what_to_drop"]
        self.current_time_list = []

    def primary_system(self, modeling: Modeling) -> None:
        t1 = time.time_ns()
        super().primary_system(modeling)
        t2  = time.time_ns()
        self.current_time_list.append(t2-t1)
    
    def emergency_system(self, modeling: Modeling) -> None:
        t1 = time.time_ns()
        super().emergency_system(modeling)
        t2  = time.time_ns()
        self.current_time_list.append(t2-t1)

    def decide(self, modeling):
        self.current_time_list = []
        return_value = super().decide(modeling)
        self.time_records.append(self.current_time_list.copy())
        return return_value
