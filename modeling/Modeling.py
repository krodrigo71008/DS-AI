import copy

from perception.ImageObject import ImageObject
from modeling.WorldModel import WorldModel
from modeling.PlayerModel import PlayerModel
from modeling.ObjectsInfo import objects_info
from modeling.constants import CAMERA_DISTANCE, CAMERA_HEADING, CAMERA_PITCH, FOV
from utility.Clock import Clock
from utility.Point2d import Point2d


class Modeling:
    def __init__(self, debug=False, queue=None, clock=Clock()):
        self.clock = clock
        self.player_model = PlayerModel(self.clock)
        self.world_model = WorldModel(self.player_model, self.clock)
        self.debug = debug
        if self.debug:
            self.records = []
            self.queue = queue

    def update_model(self, obj_list : list[ImageObject]):
        self.clock.update()
        self.world_model.update()
        self.world_model.update_local(obj_list)
        self.player_model.update()
        player_positions = [Point2d.from_box(obj.box) for obj in obj_list if objects_info.get_item_info(image_id=obj.id, info="object_type") == "PLAYER"]
        # decide which of the detected player positions is the real one
        self.world_model.decide_player_position(player_positions)
        self.world_model.start_cycle(CAMERA_HEADING, CAMERA_PITCH, CAMERA_DISTANCE, FOV)
        for obj in obj_list:
            if objects_info.get_item_info(image_id=obj.id, info="object_type") == "OBJECT":
                self.world_model.object_detected(obj)
            elif objects_info.get_item_info(image_id=obj.id, info="object_type") == "MOB":
                self.world_model.mob_detected(obj)
        self.world_model.finish_cycle()
        self.player_model.correct_error(self.world_model.avg_observed_error)
        if self.debug:
            self.records.append(copy.deepcopy((self.world_model.object_lists, self.world_model.mob_list, self.player_model)))
            #  self.queue.put(("local_objects", copy.deepcopy(self.world_model.local_objects)))
            self.queue.put(("world_model_objects", copy.deepcopy(self.world_model.object_lists)))
            self.queue.put(("fov_corners", [self.world_model.c1, self.world_model.c2, self.world_model.c3, self.world_model.c4]))
            self.queue.put(("player", copy.deepcopy(self.world_model.player)))
