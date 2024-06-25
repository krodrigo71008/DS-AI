from __future__ import annotations
from typing import TYPE_CHECKING
import math
from multiprocessing import Queue
import time

import numpy as np

from modeling.WorldModel import WorldModel, WorldModelTimer
from modeling.PlayerModel import PlayerModel, PlayerModelTimer
from modeling.ObjectsInfo import objects_info
from modeling.Slam import Slam
from modeling.constants import TILE_SIZE, PLAYER_BASE_SPEED
from perception.ImageObject import ImageObject
from utility.Clock import Clock
from utility.Point2d import Point2d
if TYPE_CHECKING:
    from perception.ImageObject import ImageObject
    from modeling.objects.ObjectModel import ObjectModel


class Modeling:
    def __init__(self, debug=False, clock=Clock()):
        self.clock = clock
        self.debug = debug
        self.latest_detected_objects : list[ImageObject] = None
        self.latest_segmentation_info : np.ndarray = None
        self.latest_yolo_timestamp : float = None
        self.latest_segmentation_timestamp : float = None
        self.received_yolo_info : bool = False
        self.received_segmentation_info : bool = False
        self.slam = Slam()
        # slam state
        self.xEst = np.array([[TILE_SIZE//2, TILE_SIZE//2]], dtype=np.float32).T
        # slam covariance
        self.PEst = np.zeros((self.slam.STATE_SIZE, self.slam.STATE_SIZE), dtype=np.float32)

        self.lm_id_to_object : list[ObjectModel] = []

        # player direction
        self._direction = None
        self.DEFAULT_SPEED = PLAYER_BASE_SPEED

        self.player_model = PlayerModel(self.clock)
        self.world_model = WorldModel(self, self.clock, debug)

        self.pests = []

    def handle_detected_objects_queue(self, detected_objects_queue: Queue) -> list[ImageObject]:
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
        
        return obj_list

    def handle_segmentation_queue(self, segmentation_queue: Queue) -> np.ndarray:
        if segmentation_queue.empty():
            segmentation_info : np.ndarray = self.latest_segmentation_info
            self.received_segmentation_info = False
        else:
            # it's very unlikely that SegmentationModel puts more than one detection in the queue before this finishes a cycle, but this is just in case
            while not segmentation_queue.empty():
                segmentation_info, timestamp = segmentation_queue.get()
                self.latest_segmentation_timestamp = timestamp
            self.received_segmentation_info = True
            self.latest_segmentation_info = segmentation_info
        
        return segmentation_info

    def update_clock(self) -> None:
        self.clock.update()

    def update_world_model(self) -> None:
        self.world_model.update()

    def update_player_model(self) -> None:
        self.player_model.update()

    def slam_predict(self) -> None:
        if self._direction is None:
            u = np.zeros((self.slam.STATE_SIZE, 1))
        else:
            u = np.array([[self.DEFAULT_SPEED*math.cos(self._direction), self.DEFAULT_SPEED*math.sin(self._direction)]]).T
        self.xEst, self.PEst = self.slam.predict(self.xEst, self.PEst, u, self.clock.dt())

    def use_received_yolo_info(self, obj_list : list[ImageObject]) -> None:
        if self.received_yolo_info:
            player_positions = [Point2d.bottom_from_box(obj.box) for obj in obj_list if objects_info.get_item_info(image_id=obj.id, info="object_type") == "PLAYER"]
            # decide which of the detected player positions is the real one
            self.world_model.decide_player_position(player_positions)

            if self._direction is None:
                past_player_position = Point2d(self.xEst[0, 0], self.xEst[1, 0])
            else:
                dt = self.latest_yolo_timestamp - self.clock.raw_timestamp()
                past_player_position = Point2d(self.xEst[0, 0], self.xEst[1, 0]) + Point2d(math.cos(self._direction), math.sin(self._direction))*dt*self.DEFAULT_SPEED
            
            observations, conv_observations, image_objs = self.world_model.handle_yolo_info(obj_list, past_player_position)
            self.xEst, self.PEst, new_objects = self.slam.update(self.xEst, self.PEst, 
                                                                 np.array([observations]).T, np.array([conv_observations]).T, 
                                                                 image_objs, self.world_model, self.lm_id_to_object)
            for image_object, slam_state_index, lm_id in new_objects:
                obj = self.world_model.create_object(image_object, slam_state_index)
                assert lm_id == len(self.lm_id_to_object)
                self.lm_id_to_object.append(obj)
                # print(self.PEst[slam_state_index:slam_state_index+2, slam_state_index:slam_state_index+2])
            self.world_model.finish_cycle()
            # print(self.xEst)
            # print(self.PEst)
            # print(self.xEst.shape)
            # print(self.PEst.shape)

    def use_received_segmentation_info(self, segmentation_info : np.ndarray) -> None:
        if self.received_segmentation_info:
            if self._direction is None:
                past_player_position = Point2d(self.xEst[0, 0], self.xEst[1, 0])
            else:
                dt = self.latest_segmentation_timestamp - self.clock.raw_timestamp()
                past_player_position = Point2d(self.xEst[0, 0], self.xEst[1, 0]) + Point2d(math.cos(self._direction), math.sin(self._direction))*dt*self.DEFAULT_SPEED
            
            self.world_model.process_segmentation_image(segmentation_info, past_player_position)

    def update_model(self, detected_objects_queue: Queue, segmentation_queue: Queue):
        obj_list = self.handle_detected_objects_queue(detected_objects_queue)
        segmentation_info = self.handle_segmentation_queue(segmentation_queue)

        return self.update_model_using_info(obj_list, segmentation_info)

    def update_model_using_info(self, obj_list : list[ImageObject], segmentation_info : np.ndarray):
        self.update_clock()
        self.update_world_model()
        self.update_player_model()
        self.slam_predict()
        self.use_received_yolo_info(obj_list)
        self.use_received_segmentation_info(segmentation_info)
        
        # if self.debug:
        #     self.pests.append(self.PEst.copy())

        if self.debug:
            return ([(class_name, [(obj.position(), obj.std()) for obj in obj_list]) for class_name, obj_list in self.world_model.object_lists.items()], 
                    [self.world_model.c1, self.world_model.c2, self.world_model.c3, self.world_model.c4], 
                    (Point2d(self.xEst[0, 0], self.xEst[1, 0]), (self.PEst[0, 0], self.PEst[1, 1])), 
                    self.world_model.tile_manager)

    def remove_from_slam_state(self, slam_state_index : int):
        self.xEst = np.concatenate((self.xEst[:slam_state_index], self.xEst[slam_state_index+self.slam.LM_SIZE:]))
        self.PEst = np.vstack((
            np.hstack((self.PEst[:slam_state_index, :slam_state_index], self.PEst[:slam_state_index, slam_state_index+self.slam.LM_SIZE:])),
            np.hstack((self.PEst[slam_state_index+self.slam.LM_SIZE:, :slam_state_index], self.PEst[slam_state_index+self.slam.LM_SIZE:, slam_state_index+self.slam.LM_SIZE:]))
        ))

    def player_position(self) -> Point2d:
        return Point2d(self.xEst[0, 0], self.xEst[1, 0])

    def player_std(self) -> tuple[float, float]:
        return (self.PEst[0, 0], self.PEst[1, 1])

    def set_player_position(self, pos : Point2d) -> None:
        self.xEst[0, 0] = pos.x1
        self.xEst[1, 0] = pos.x2

    def set_direction(self, direction : float) -> None:
        self._direction = direction

class ModelingRecorder(Modeling):
    def __init__(self, debug=False, clock=Clock()):
        super().__init__(debug, clock)
        self.all_direction_changes : list[float] = []
        self.all_direction_changes_timestamps : list[float] = []

    def set_direction(self, direction: float) -> None:
        self.all_direction_changes.append(direction)
        self.all_direction_changes_timestamps.append(self.clock.raw_timestamp())
        return super().set_direction(direction)

class ModelingTimer(Modeling):
    def __init__(self, debug=False, clock=Clock()):
        super().__init__(debug, clock)
        self.player_model = PlayerModelTimer(self.clock)
        self.world_model = WorldModelTimer(self, self.clock, debug)
        self.time_records = []
        self.split_names = ["handle_detected_objects_queue", "handle_segmentation_queue", "update_clock", "update_world_model",
                            "update_player_model", "slam_predict", "use_received_yolo_info", "use_received_segmentation_info", "total"]
        self.current_time_list = []
        self.slam_dts = []

    def handle_detected_objects_queue(self, detected_objects_queue: Queue) -> list[ImageObject]:
        t1 = time.time_ns()
        return_value = super().handle_detected_objects_queue(detected_objects_queue)
        t2  = time.time_ns()
        self.current_time_list.append(t2-t1)
        return return_value
    
    def handle_segmentation_queue(self, segmentation_queue: Queue) -> np.ndarray:
        t1 = time.time_ns()
        return_value = super().handle_segmentation_queue(segmentation_queue)
        t2  = time.time_ns()
        self.current_time_list.append(t2-t1)
        return return_value
    
    def update_clock(self) -> None:
        t1 = time.time_ns()
        super().update_clock()
        t2  = time.time_ns()
        self.current_time_list.append(t2-t1)
    
    def update_world_model(self) -> None:
        t1 = time.time_ns()
        super().update_world_model()
        t2  = time.time_ns()
        self.current_time_list.append(t2-t1)
    
    def update_player_model(self) -> None:
        t1 = time.time_ns()
        super().update_player_model()
        t2  = time.time_ns()
        self.current_time_list.append(t2-t1)
    
    def slam_predict(self) -> None:
        t1 = time.time_ns()
        super().slam_predict()
        t2  = time.time_ns()
        self.slam_dts.append(self.clock.dt())
        self.current_time_list.append(t2-t1)
    
    def use_received_yolo_info(self, obj_list: list[ImageObject]) -> None:
        t1 = time.time_ns()
        super().use_received_yolo_info(obj_list)
        t2  = time.time_ns()
        self.current_time_list.append(t2-t1)
    
    def use_received_segmentation_info(self, segmentation_info: np.ndarray) -> None:
        t1 = time.time_ns()
        super().use_received_segmentation_info(segmentation_info)
        t2  = time.time_ns()
        self.current_time_list.append(t2-t1)
    
    def update_model(self, detected_objects_queue: Queue, segmentation_queue: Queue):
        self.current_time_list = []
        t1 = time.time_ns()
        return_value = super().update_model(detected_objects_queue, segmentation_queue)
        t2 = time.time_ns()
        self.current_time_list.append(t2-t1)
        self.time_records.append(self.current_time_list.copy())
        return return_value

    def update_model_using_info(self, obj_list: list[ImageObject], segmentation_info: np.ndarray):
        return_value = super().update_model_using_info(obj_list, segmentation_info)
        # this condition only happens if update_model() wasn't called before this
        # aka run_with_recorded_inputs
        if len(self.current_time_list) == 6:
            # this just makes it so length is the usual 9
            self.current_time_list.insert(-1, 0)
            self.current_time_list.insert(-1, 0)
        return return_value
