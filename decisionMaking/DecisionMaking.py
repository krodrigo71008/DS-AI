import math

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
        self.debug : bool = debug
        if self.debug:
            self.records = []

    # decides the action (high level)
    # should be called every loop
    def primary_system(self, modeling: Modeling) -> None:
        self.behavior_tree.update(modeling, self.action_requester)
        self.primary_action = self.action_requester.get_action()

    # decides minor steps for the primary system action
    def secondary_system(self, modeling: Modeling) -> None:
        if self.primary_action[0] == "gather":
            items = self.primary_action[1].copy()
            counts = modeling.player_model.inventory.get_inventory_count(["CutGrass", "Twigs"])
            # if we have at least 4 CutGrass, that's enough
            if "CutGrass" in items and counts[0] >= 4:
                items.remove("CutGrass")
            # if we have at least 4 Twigs, that's enough
            if "Twigs" in items and counts[1] >= 4:
                items.remove("Twigs")
            world = modeling.world_model
            # if we want food, we should look for these things
            if "food" in items:
                items.remove("food")
                items.extend(["BerryBush", "Honey", "Carrot"])
            if "CutGrass" in items:
                items.append("Grass")
            if "Twigs" in items:
                items.append("Sapling")
            # we should only look for plants that are not harvested
            obj_lists = world.get_all_of(items, filter_="only_not_harvested")
            all_objects = []
            for obj_list in obj_lists.values():
                all_objects = [*all_objects, *obj_list]
            locations = [obj.position for obj in all_objects]
            if len(locations) == 0:
                self.secondary_action = ("explore", modeling.world_model)
            else:
                self.choose_destination(locations, modeling.world_model.player.position, all_objects)
        elif self.primary_action[0] == "craft":
            self.secondary_action = ("craft", self.primary_action[1])
        elif self.primary_action[0] == "unequip":
            self.secondary_action = ("unequip", "Hand")

    # takes control when needed
    def emergency_system(self, modeling: Modeling) -> None:
        # if hunger is too low
        if modeling.player_model.hunger < 30:
            foods = ["Seeds", "MonsterMeat", "Honey", "FrogLegs", "Meat", "Berries"]
            food_counts = modeling.player_model.inventory.get_inventory_count(foods)
            # if we have no food, look for it
            if np.array(food_counts).sum() == 0:
                self.primary_action = ("gather", ["food"])
                self.secondary_system(modeling)
            else:
                if modeling.player_model.hunger < 15:
                    hunger_points_to_fill = modeling.player_model.max_hunger - modeling.player_model.hunger
                    self.decide_what_to_eat(foods, food_counts, hunger_points_to_fill)
        # if it's nighttime
        elif modeling.clock.day_section() == "Night":
            torch_count = modeling.player_model.inventory.get_inventory_count(["Torch"])
            # this will fail if we don't have materials to craft it, but we should have enough
            if np.array(torch_count).sum() == 0:
                self.secondary_action = ("craft", ["Torch"])
            else:
                if type(modeling.player_model.inventory.hand.object).__name__ != "Torch":
                    self.secondary_action = ("equip", ["Torch"])
        else:
            monsters = [
                "Treeguard", "KillerBee", "Frog", "Hound", "IceHound", "FireHound", "Spider", "SpiderWarrior",
                "Tallbird", "Ghost", "GuardianPig", "Merm", "Tentacle", "ClockRook", "ClockKnight", "ClockBishop",
                "Nightmare1", "Nightmare2", "Werepig", "Mosquito"
            ]
            monster_lists = modeling.world_model.get_all_of(monsters)
            all_objects = []
            for monster_list in monster_lists.values():
                all_objects = [*all_objects, *monster_list]
            locations = [obj.position for obj in all_objects]
            distances = [location.distance(modeling.player_model.position) for location in locations]
            if len(distances) > 0:
                closest_index = min(range(len(distances)), key=distances.__getitem__)
                if distances[closest_index] < MONSTER_DANGER_DISTANCE:
                    self.run_away_from(locations[closest_index], modeling.player_model.position)

    # helps with inventory management
    def inventory_management_system(self, modeling: Modeling) -> None:
        pass

    def choose_destination(self, objectives: list[Point2d], player_position: Point2d,
                           all_objects: list[ObjectModel]) -> None:
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
            # if we're currently trying to pick up an item, I don't want to revert trying to get close to it unless
            # we're really far away
            if self.secondary_action[0] == "pick_up_item":
                if closest_distance > 1.5*PICK_UP_DISTANCE:
                    self.secondary_action = ("go_to", closest)
                else:
                    if self.secondary_action[1] != all_objects[closest_index]:
                        self.secondary_action = ("pick_up_item", all_objects[closest_index])
            else:
                self.secondary_action = ("go_to", closest)

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
        self.secondary_action = ("eat", best_food_and_count[0])

    def run_away_from(self, danger_position: Point2d, player_position: Point2d) -> None:
        # direction_to_run in radians
        direction_to_run = (player_position - danger_position).angle()
        self.secondary_action = ("run", direction_to_run)

    @staticmethod
    def textify(secondary_action):
        aux_str = ""
        if secondary_action[0] == "run":
            aux_str = f"{secondary_action[1]/math.pi*180}°"
        elif secondary_action[0] == "go_to":
            aux_str = (secondary_action[1].x1, secondary_action[1].x2)
        elif secondary_action[0] == "pick_up_item":
            aux_str = (secondary_action[1], secondary_action[1]._state)
        elif (secondary_action[0] == "eat" or secondary_action[0] == "pick_up_item" 
            or secondary_action[0] == "explore" or secondary_action[0] == "equip" or secondary_action[0] == "craft"
            ):
            aux_str = secondary_action[1]
        return (secondary_action[0], aux_str)

    # main function that should be called
    def decide(self, modeling):
        self.primary_system(modeling)
        self.secondary_system(modeling)
        self.inventory_management_system(modeling)
        self.emergency_system(modeling)
        if self.debug:
            self.records.append((self.primary_action, self.textify(self.secondary_action)))
            return (self.primary_action, self.secondary_action)
