import copy

from modeling.WorldModel import WorldModel
from modeling.PlayerModel import PlayerModel
from modeling.ObjectsInfo import objects_info
from utility.Clock import Clock
from utility.Point2d import Point2d


class Modeling:
    def __init__(self, debug=False, queue=None):
        self.clock = Clock()
        self.player_model = PlayerModel(self.clock)
        self.world_model = WorldModel(self.player_model, self.clock)
        self.debug = debug
        if self.debug:
            self.records = []
            self.queue = queue

    def update_model(self, obj_list):
        self.clock.update()
        self.world_model.update()
        self.world_model.update_local(obj_list)
        self.player_model.update()
        for obj in obj_list:
            if objects_info.get_item_info(image_id=obj.id, info="object_type") == "PLAYER":
                # the world model uses the player position on screen to improve the transformations
                self.world_model.player_detected(Point2d(obj.box[0] + obj.box[2]//2, obj.box[1] + obj.box[3]))
        self.world_model.update_origin_position()
        for obj in obj_list:
            if objects_info.get_item_info(image_id=obj.id, info="object_type") == "PLAYER":
                self.player_model.player_detected(obj)
            elif objects_info.get_item_info(image_id=obj.id, info="object_type") == "OBJECT":
                self.world_model.object_detected(obj)
            elif objects_info.get_item_info(image_id=obj.id, info="object_type") == "MOB":
                self.world_model.mob_detected(obj)
        self.world_model.finish_cycle()
        if self.debug:
            self.records.append(copy.deepcopy((self.world_model.object_lists, self.world_model.mob_list, self.player_model)))
            self.queue.put(("detected_objects", copy.deepcopy(self.world_model.local_objects)))
            self.queue.put(("world_model_objects", copy.deepcopy(self.world_model.object_lists)))
            self.queue.put(("player", copy.deepcopy(self.world_model.player)))
