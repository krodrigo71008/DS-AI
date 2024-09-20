import random
import math

import numpy as np
from shapely.geometry import Polygon, box
from PIL import Image

from perception.constants import SCREEN_SIZE
from perception.ImageObject import ImageObject
from modeling.Modeling import Modeling
from modeling.constants import PLAYER_BASE_SPEED, CAMERA_HEADING, TILE_SIZE
from modeling.utility import image_to_local_position
from decisionMaking.DecisionMaking import DecisionMaking
from control.Control import Control
from utility.utility import is_inside_convex_polygon, clamp2pi
from utility.Point2d import Point2d
from utility.Clock import ClockFake
from utility.Visualizer import Visualizer


class FakeObjectModel():
    def __init__(self, id_) -> None:
        self.image_id = id_

class FakeModeling():
    def __init__(self, player_position : Point2d) -> None:
        self._player_pos = player_position

    def player_position(self):
        return self._player_pos
    
    def set_direction(self, angle : float):
        pass

class DecisionMakingSimulator():
    def __init__(self, runtime : float = 20.0) -> None:
        self.PLAYER_SPEED = PLAYER_BASE_SPEED
        self.start_point = Point2d(2, 2)
        self.DT = 0.1
        self.landmarks : list[tuple[int, Point2d]] = [

        ]
        self.max_runtime = runtime
        self.clock = ClockFake()
        self.modeling = Modeling(clock=self.clock)
        self.decision_making = DecisionMaking()
        self.control = Control(clock=self.clock)
        self.visualizer = Visualizer()
        self.tiles : np.ndarray = np.zeros((100, 100))
        rev_color_dict = {}
        for i, item in self.visualizer.segmentation_color_dict.items():
            if item[0] is not None:
                rev_color_dict[(item[0][0], item[0][1], item[0][2])] = i
        with Image.open("test_terrain.png", "r") as image:
            aux = np.array(image)
            for i in range(image.size[0]):
                for j in range(image.size[1]):
                    self.tiles[i, j] = rev_color_dict[(aux[i, j, 0], aux[i, j, 1], aux[i, j, 2])]
        self.tiles_offset : tuple[int, int] = (-50, -50)

        self.modeling.world_model.tile_manager.tiles = np.zeros((self.tiles.shape[0], 
                                                                 self.tiles.shape[1], 
                                                                 self.modeling.world_model.tile_manager._MAX_QUEUE_SIZE))
        self.modeling.world_model.tile_manager._x1_shift = self.tiles_offset[0]
        self.modeling.world_model.tile_manager._x2_shift = self.tiles_offset[1]

        c1 = image_to_local_position(Point2d(0, 0))
        c2 = image_to_local_position(Point2d(0, SCREEN_SIZE["height"]))
        c3 = image_to_local_position(Point2d(SCREEN_SIZE["width"], SCREEN_SIZE["height"]))
        c4 = image_to_local_position(Point2d(SCREEN_SIZE["width"], 0))
        self.vision_trapezoid = [c1, c2, c3, c4, c1]
        self.tile_search_range = (int(min(c1.x1, c2.x1, c3.x1, c4.x1)//TILE_SIZE) - 2,
                                  int(max(c1.x1, c2.x1, c3.x1, c4.x1)//TILE_SIZE) + 2,
                                  int(min(c1.x2, c2.x2, c3.x2, c4.x2)//TILE_SIZE) - 2,
                                  int(max(c1.x2, c2.x2, c3.x2, c4.x2)//TILE_SIZE) + 2)


    def get_tile(self, tile : tuple[int, int]):
        i, j = tile
        return self.tiles[i - self.tiles_offset[0], j - self.tiles_offset[1]]
            
    def _is_tile_visible(self, tile : tuple[int, int], player_position : Point2d) -> bool:
        i, j = tile
        aux = [
            (self.vision_trapezoid[0].x1 + player_position.x1, self.vision_trapezoid[0].x2 + player_position.x2),
            (self.vision_trapezoid[1].x1 + player_position.x1, self.vision_trapezoid[1].x2 + player_position.x2),
            (self.vision_trapezoid[2].x1 + player_position.x1, self.vision_trapezoid[2].x2 + player_position.x2),
            (self.vision_trapezoid[3].x1 + player_position.x1, self.vision_trapezoid[3].x2 + player_position.x2),
            ]
        translated_trapezium = Polygon(aux)
        tile_square = box(i*TILE_SIZE, j*TILE_SIZE, i*TILE_SIZE+TILE_SIZE, j*TILE_SIZE+TILE_SIZE)
        intersection = tile_square.intersection(translated_trapezium).area/TILE_SIZE/TILE_SIZE
        return intersection >= 0.5

    def update_segmentation_info(self) -> None:
        player_tile_i = int(self.modeling.player_position().x1//TILE_SIZE)
        player_tile_j = int(self.modeling.player_position().x2//TILE_SIZE)
        for i in range(player_tile_i+self.tile_search_range[0], player_tile_i+self.tile_search_range[1]):
            for j in range(player_tile_j+self.tile_search_range[2], player_tile_j+self.tile_search_range[3]):
                if self._is_tile_visible((i, j), self.modeling.player_position()):
                    self.modeling.world_model.tile_manager.add_tile((i, j), self.get_tile((i, j)))

    def _get_visible_landmarks(self, player_position : Point2d) -> list[tuple[int, Point2d]]:
        results = []
        for lm in self.landmarks:
            # check if landmark relative position is "on screen"
            if is_inside_convex_polygon(self.vision_trapezoid, lm[1]-player_position):
                results.append(lm)
        
        return results
    
    def generate_observations(self, player_position : Point2d) -> list[ImageObject]:
        landmarks = self._get_visible_landmarks(player_position)
        obs = []
        for id_, lm in landmarks:
            result = self.modeling.world_model.H_function(lm.x1 - player_position.x1, lm.x2 - player_position.x2)
            xz_point = image_to_local_position(result)
            obs.append(ImageObject(id_, 1.0, [xz_point.x1, xz_point.x1, 1, 1]))

        return obs

    def convert_keys_to_angle(self, keys : list[str]):
        if keys == ["w"]:
            angle = -180
        elif keys == ["w", "a"]:
            angle = -135
        elif keys == ["a"]:
            angle = -90
        elif keys == ["s", "a"]:
            angle = -45
        elif keys == ["s"]:
            angle = 0
        elif keys == ["s", "d"]:
            angle = 45
        elif keys == ["d"]:
            angle = 90
        elif keys == ["w", "d"]:
            angle = 135
        else:
            # this should never happen
            raise Exception("Invalid keys!")
        
        angle += CAMERA_HEADING
        angle *= math.pi/180
        angle = clamp2pi(angle)
        return angle


    def step(self):
        print(f"{self.clock.time_in_seconds:.1f}/{self.max_runtime}")
        self.clock.time_in_seconds += self.DT
        self.clock._last_dt = self.DT
        self.clock._last_time += self.DT

        if self.clock.time_in_seconds > self.max_runtime:
            return False

        if self.control.key_action is not None:
            keys = self.control.key_action[0]
            direction = self.convert_keys_to_angle(keys)
            speed_gt = Point2d(self.PLAYER_SPEED*math.cos(direction), self.PLAYER_SPEED*math.sin(direction))
            new_player_pos = self.modeling.player_position() + speed_gt*self.DT
            self.modeling.set_player_position(new_player_pos)

        self.modeling.update_player_model()
        observations = self.generate_observations(self.modeling.player_position())
        self.modeling.latest_yolo_timestamp = self.clock.raw_timestamp()
        self.modeling.received_yolo_info = True
        self.modeling.use_received_yolo_info(observations)
        self.update_segmentation_info()
        self.decision_making.decide(self.modeling)
        self.control.control(self.decision_making, self.modeling)

        if self.modeling.world_model.latest_debug_image is not None:
            self.visualizer.draw_world_model_image(self.modeling.world_model.latest_debug_image)
        self.visualizer.update_world_model(self.modeling)
        self.visualizer.draw_time(self.clock.time())
        self.visualizer.write_decision_making_control(self.decision_making, self.control)
        self.visualizer.draw_objective_point(self.modeling.player_position(), self.control)
        self.visualizer.reset()

        return True

    def run(self):
        while True:
            if not self.step():
                break
