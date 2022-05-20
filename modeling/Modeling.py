import copy

from modeling.WorldModel import WorldModel
from modeling.PlayerModel import PlayerModel
from modeling.ObjectsInfo import objects_info
from utility.Clock import Clock


class Modeling:
    def __init__(self, debug=False):
        self.clock = Clock()
        self.player_model = PlayerModel(self.clock)
        self.world_model = WorldModel(self.player_model, self.clock)
        if debug:
            self.records = []
            self.debug = True
        else:
            self.debug = False

    def update_model(self, obj_list):
        self.clock.update()
        self.world_model.update()
        self.player_model.update()
        for obj in obj_list:
            if objects_info.get_item_info(image_id=obj.id, info="object_type") == "PLAYER":
                self.player_model.player_detected(obj)
            elif objects_info.get_item_info(image_id=obj.id, info="object_type") == "OBJECT":
                self.world_model.object_detected(obj)
            elif objects_info.get_item_info(image_id=obj.id, info="object_type") == "MOB":
                self.world_model.mob_detected(obj)
        if self.debug:
            self.records.append(copy.deepcopy((self.world_model.object_lists, self.world_model.mob_list, self.player_model)))
