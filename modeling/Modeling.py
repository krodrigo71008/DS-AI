import copy
from multiprocessing import Queue
import time

import numpy as np

from perception.ImageObject import ImageObject
from modeling.WorldModel import WorldModel
from modeling.PlayerModel import PlayerModel, PlayerModelRecorder
from modeling.ObjectsInfo import objects_info
from utility.Clock import Clock
from utility.Point2d import Point2d


class Modeling:
    def __init__(self, debug=False, clock=Clock(), measure_time=False):
        self.clock = clock
        self.player_model = PlayerModel(self.clock, measure_time)
        self.world_model = WorldModel(self.player_model, self.clock, debug, measure_time)
        self.debug = debug
        self.latest_detected_objects : list[ImageObject] = None
        self.latest_segmentation_info : np.array = None
        self.latest_yolo_timestamp : float = None
        self.latest_segmentation_timestamp : float = None
        self.received_yolo_info : bool = False
        self.received_segmentation_info : bool = False
        self.measure_time = measure_time
        if self.measure_time:
            self.time_records = []
            self.split_names = ["handle_detected_objects_queue", "handle_segmentation_queue", "update_clock", 
                                "update_world_model", "update_player_model", "use_received_yolo_info", "use_received_segmentation_info"]

    def update_model(self, detected_objects_queue: Queue, segmentation_queue: Queue):
        if self.measure_time:
            t1 = time.time_ns()

        if detected_objects_queue.empty():
            obj_list : list[ImageObject] = self.latest_detected_objects
            self.received_yolo_info = False
        else:
            # it's very unlikely that Perception puts more than one detection in the queue before this finishes a cycle, but this is just in case
            while not detected_objects_queue.empty():
                obj_list, timestamp = detected_objects_queue.get()
                self.latest_yolo_timestamp = timestamp
            self.received_yolo_info = True
            self.latest_detected_objects = obj_list

        if self.measure_time:
            t2 = time.time_ns()

        
        if segmentation_queue.empty():
            segmentation_info : list[ImageObject] = self.latest_segmentation_info
            self.received_segmentation_info = False
        else:
            # it's very unlikely that SegmentationModel puts more than one detection in the queue before this finishes a cycle, but this is just in case
            while not segmentation_queue.empty():
                segmentation_info, timestamp = segmentation_queue.get()
                self.latest_segmentation_timestamp = timestamp
            self.received_segmentation_info = True
            self.latest_segmentation_info = segmentation_info

        if self.measure_time:
            t3 = time.time_ns()
            self.time_records.append([t2-t1, t3-t2])

        return self.update_model_using_info(obj_list, segmentation_info)


    def update_model_using_info(self, obj_list : list[ImageObject], segmentation_info : np.array) -> None:
        if self.measure_time:
            t4 = time.time_ns()

        self.clock.update()

        if self.measure_time:
            t5 = time.time_ns()

        self.world_model.update()

        if self.measure_time:
            t6 = time.time_ns()

        self.player_model.update()

        if self.measure_time:
            t7 = time.time_ns()

        if self.received_yolo_info:
            self.world_model.yolo_timestamp = self.latest_yolo_timestamp
            player_positions = [Point2d.bottom_from_box(obj.box) for obj in obj_list if objects_info.get_item_info(image_id=obj.id, info="object_type") == "PLAYER"]
            # decide which of the detected player positions is the real one
            self.world_model.decide_player_position(player_positions)
            self.world_model.start_cycle()
            for obj in obj_list:
                if objects_info.get_item_info(image_id=obj.id, info="object_type") == "OBJECT":
                    self.world_model.object_detected(obj)
                elif objects_info.get_item_info(image_id=obj.id, info="object_type") == "MOB":
                    self.world_model.mob_detected(obj)
            self.world_model.finish_cycle()
            self.player_model.correct_error(self.world_model.avg_observed_error)

        if self.measure_time:
            t8 = time.time_ns()

        if self.received_segmentation_info:
            self.world_model.segmentation_timestamp = self.latest_segmentation_timestamp
            self.world_model.process_segmentation_image(segmentation_info)

        if self.measure_time:
            t9 = time.time_ns()
            # this condition only happens if update_model() wasn't called before this
            if len(self.time_records) == 0 or len(self.time_records[-1]) != 2:
                self.time_records.append([-1, -1])
            self.time_records[-1].extend([t5-t4, t6-t5, t7-t6, t8-t7, t9-t8])

        if self.debug:
            return ([(class_name, [obj.position for obj in obj_list]) for class_name, obj_list in self.world_model.object_lists.items()], 
                    [self.world_model.c1, self.world_model.c2, self.world_model.c3, self.world_model.c4], 
                    self.world_model.player.position, 
                    self.world_model.tiles)

class ModelingRecorder(Modeling):
    def __init__(self, debug=False, clock=Clock()):
        super().__init__(debug, clock)
        self.player_model = PlayerModelRecorder(self.clock)
        self.world_model = WorldModel(self.player_model, self.clock)
