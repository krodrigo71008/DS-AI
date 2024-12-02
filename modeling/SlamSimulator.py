import random
import math
from PIL import Image, ImageFont, ImageDraw
import os
import time

import numpy as np

from perception.constants import SCREEN_SIZE
from perception.ImageObject import ImageObject
from modeling.Modeling import Modeling
from modeling.WorldModel import WorldModelSlamMock
from modeling.Slam import SlamTimer
from modeling.constants import PLAYER_BASE_SPEED, CAMERA_HEADING
from modeling.utility import image_to_local_position
from control.constants import CLOSE_ENOUGH_DISTANCE
from control.Control import Control
from utility.utility import is_inside_convex_polygon, clamp2pi
from utility.Point2d import Point2d
from utility.Clock import Clock


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

class SlamSimulator():
    def __init__(self, seed : int, num_landmarks : int, trajectory : list[Point2d], 
                 u_noise : list[float], h_noise : list[float], debug : bool = False, save_images : bool = False, 
                 randomize : bool = False, closed_control_loop : bool = True) -> None:
        assert num_landmarks >= 0
        assert len(u_noise) == 2
        assert len(h_noise) == 2
        self.trajectory = trajectory
        self.PLAYER_SPEED = PLAYER_BASE_SPEED
        self.start_point = Point2d(0, 0)
        self.start_time = 0.0
        self.trajectory_index = 0
        self.DT = 0.1
        self.x_range = (-100, 100)
        self.y_range = (-100, 100)
        random.seed(seed)
        if not randomize:
            np.random.seed(seed)
        self.landmarks : list[tuple[int, Point2d]] = []
        for _ in range(num_landmarks):
            self.landmarks.append((random.randint(0, 50), Point2d(self.generate_random_in_range(self.x_range), self.generate_random_in_range(self.y_range))))
        
        self.world_model = WorldModelSlamMock(Modeling(), Clock())
        c1 = image_to_local_position(Point2d(0, 0))
        c2 = image_to_local_position(Point2d(0, SCREEN_SIZE["height"]))
        c3 = image_to_local_position(Point2d(SCREEN_SIZE["width"], SCREEN_SIZE["height"]))
        c4 = image_to_local_position(Point2d(SCREEN_SIZE["width"], 0))
        self.vision_trapezoid = [c1, c2, c3, c4, c1]
        self.slam = SlamTimer()
        # slam state
        self.xEst = np.array([[self.start_point.x1, self.start_point.x2]], dtype=np.float32).T
        # slam covariance
        self.PEst = np.zeros((self.slam.STATE_SIZE, self.slam.STATE_SIZE), dtype=np.float32)
        self.control = Control()

        self.player_position_gt = self.start_point
        self.player_position_gt_list = []
        self.player_position_gt_list.append([self.start_point.x1, self.start_point.x2])
        self.state_estimate_list = []
        self.state_estimate_list.append(self.xEst.copy())
        self.covariance_estimate_list = []
        self.covariance_estimate_list.append(self.PEst.copy())
        self.time = 0.0
        self.u_noise = np.diag(u_noise)
        self.h_noise = np.diag(h_noise)
        self.lm_id_to_object = {}

        self.measurement_errors = []
        self.measurement_position_errors = []
        self.speed_errors = []
        self.visible_landmarks = []

        self.landmarks_that_got_visible = []

        self.debug = debug
        self.save_images = save_images
        if self.save_images:
            self.xEst_before_predict = None
            self.PEst_before_predict = None
            self.xEst_before_update = None
            self.PEst_before_update = None
        
        if self.save_images:
            self.image = Image.new(mode="RGB", size=(SCREEN_SIZE["width"], SCREEN_SIZE["width"]), color="white")
            self.draw = ImageDraw.Draw(self.image)

        self.closed_control_loop = True
        if not closed_control_loop:
            self.closed_control_loop = False
            self.turn_times = []
            self.turn_angles = []
            point = self.start_point
            time_acc = 0
            for target in self.trajectory:
                distance = point.distance(target)
                time_ = distance/self.PLAYER_SPEED
                angle = (target - point).angle()
                point = target
                time_acc += time_
                self.turn_times.append(time_acc)
                self.turn_angles.append(angle)
            
    @staticmethod
    def generate_random_in_range(range_ : tuple[float, float]) -> float:
        start, end = range_
        return random.random()*(end-start) + start

    def _get_visible_landmarks(self, player_position : Point2d) -> list[tuple[int, Point2d]]:
        results = []
        for lm in self.landmarks:
            # check if landmark relative position is "on screen"
            if is_inside_convex_polygon(self.vision_trapezoid, lm[1]-player_position):
                results.append(lm)
                if self.debug:
                    if lm not in self.landmarks_that_got_visible:
                        self.landmarks_that_got_visible.append(lm)
        
        return results
    
    def generate_observations(self, player_position : Point2d) -> tuple[np.ndarray, np.ndarray, list[ImageObject], list[Point2d]]:
        landmarks = self._get_visible_landmarks(player_position)
        if self.debug:
            self.visible_landmarks.append(len(landmarks))
        xz_temp_arr = []
        obs_temp_arr = []
        image_objs = []
        lm_points = []
        for id_, lm in landmarks:
            result = self.world_model.H_function(lm.x1 - player_position.x1, lm.x2 - player_position.x2)
            measurement_error_u = np.random.randn()*self.h_noise[0, 0]
            measurement_error_v = np.random.randn()*self.h_noise[1, 1]
            if self.debug:
                self.measurement_errors.append([measurement_error_u, measurement_error_v])
            noisy_point = Point2d(result[0] + measurement_error_u, result[1] + measurement_error_v)
            xz_point = image_to_local_position(noisy_point)
            if self.debug:
                self.measurement_position_errors.append([player_position.x1 + xz_point.x1 - lm.x1, 
                                                        player_position.x2 + xz_point.x2 - lm.x2])
            xz_temp_arr.extend([xz_point.x1, xz_point.x2])
            obs_temp_arr.extend([noisy_point.x1, noisy_point.x2])
            image_objs.append(ImageObject(id_, 0.0, [0, 0, 0, 0]))
            lm_points.append(lm)

        return np.array([obs_temp_arr]).T, np.array([xz_temp_arr]).T, image_objs, lm_points

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
        self.time += self.DT
        if self.closed_control_loop:
            if self.player_position_gt.distance(self.trajectory[self.trajectory_index]) < CLOSE_ENOUGH_DISTANCE:
                self.trajectory_index += 1
        else:
            if self.time > self.turn_times[self.trajectory_index]:
                self.trajectory_index += 1
        
        if self.trajectory_index >= len(self.trajectory):
            return False
        if self.closed_control_loop:
            self.control.go_precisely_towards(self.trajectory[self.trajectory_index], FakeModeling(self.player_position_gt))
        else:
            self.control.run(self.turn_angles[self.trajectory_index], FakeModeling(self.player_position_gt))

        keys = self.control.key_action[0]
        direction = self.convert_keys_to_angle(keys)
        speed_gt = Point2d(self.PLAYER_SPEED*math.cos(direction), self.PLAYER_SPEED*math.sin(direction))
        u = np.array([[speed_gt.x1, speed_gt.x2]]).T
        speed_x_error = np.random.randn()*self.u_noise[0, 0]
        speed_z_error = np.random.randn()*self.u_noise[1, 1]
        speed_gt += Point2d(speed_x_error, speed_z_error)
        if self.debug:
            self.speed_errors.append([speed_x_error, speed_z_error])
        self.player_position_gt += speed_gt*self.DT
        if self.debug:
            self.player_position_gt_list.append([self.player_position_gt.x1, self.player_position_gt.x2])
        if self.save_images:
            self.xEst_before_predict = self.xEst.copy()
            self.PEst_before_predict = self.PEst.copy()
        self.xEst, self.PEst = self.slam.predict(self.xEst, self.PEst, u, self.DT)

        if self.debug:
            previous_visible_lm = len(self.landmarks_that_got_visible)

        observations, conv_observations, image_objs, lm_points = self.generate_observations(self.player_position_gt)

        if self.debug:
            updated_visible_lm = len(self.landmarks_that_got_visible)
            new_visible_lm = updated_visible_lm - previous_visible_lm
            prev_state_size = self.xEst.shape[0]

        if self.save_images:
            self.xEst_before_update = self.xEst.copy()
            self.PEst_before_update = self.PEst.copy()
        

        self.xEst, self.PEst, new_objects = self.slam.update(self.xEst, self.PEst, observations, conv_observations, 
                                                             image_objs, self.world_model, self.lm_id_to_object, lm_points)
        
        # updated_state_size = self.xEst.shape[0]
        # new_lm_added_to_state = (updated_state_size - prev_state_size)//2

        # if new_lm_added_to_state != new_visible_lm:
        #     mahal_dists = []
        #     for i in range(new_lm_added_to_state):
        #         for j in range(self.xEst.shape[0]//2 - 1):
        #             j_idx = 2+j*2
        #             if i == 0:
        #                 mahal_dists.append(self.slam.mahal_dist(self.xEst[j_idx:j_idx+2], self.xEst[-2:], self.PEst[j_idx:j_idx+2, j_idx:j_idx+2]))
        #             else:
        #                 mahal_dists.append(self.slam.mahal_dist(self.xEst[j_idx:j_idx+2], self.xEst[-2*(i+1):-2*i], self.PEst[j_idx:j_idx+2, j_idx:j_idx+2]))

        #     print(f"{new_lm_added_to_state} added, {new_visible_lm} newly visible")

        if self.debug:
            self.state_estimate_list.append(self.xEst.copy())
            self.covariance_estimate_list.append(self.PEst.copy())
        for image_object, slam_state_index, lm_id in new_objects:
            obj = FakeObjectModel(image_object.id)
            self.lm_id_to_object[lm_id] = obj

        return True

    def save_state_image(self):
        os.makedirs("slam_simulator_results/images", exist_ok=True)
        x_min = min([p.x1 for p in self.vision_trapezoid])
        x_max = max([p.x1 for p in self.vision_trapezoid])
        z_min = min([p.x2 for p in self.vision_trapezoid])
        z_max = max([p.x2 for p in self.vision_trapezoid])
        x_range = (x_max - x_min)*1.5
        z_range = (z_max - z_min)*1.5
        x_mean = (x_min + x_max)/2
        z_mean = (z_min + z_max)/2
        
        xests = [self.xEst_before_predict, self.xEst_before_update, self.xEst]
        pests = [self.PEst_before_predict, self.PEst_before_update, self.PEst]
        names = ["a_before_predict", "b_before_update", "c_after_update"]


        for xest, pest, name in zip(xests, pests, names):
            player_x_estimate = xest[0, 0]
            player_z_estimate = xest[1, 0]
            visible_x_range = (player_x_estimate + x_mean - x_range/2, player_x_estimate + x_mean + x_range/2)
            visible_z_range = (player_z_estimate + z_mean - z_range/2, player_z_estimate + z_mean + z_range/2)
            x_gt = self.player_position_gt.x1
            z_gt = self.player_position_gt.x2
            self.draw_position(x_gt, z_gt, visible_x_range, visible_z_range, player=True)
            x = xest[0, 0]
            z = xest[1, 0]
            cov_x = pest[0, 0]
            cov_z = pest[1, 1]
            self.draw_estimate_with_covariance(x, z, cov_x, cov_z, visible_x_range, visible_z_range, player=True)
            for image_id, lm in self.landmarks:
                self.draw_position(lm.x1, lm.x2, visible_x_range, visible_z_range)
                
            for lm_id in range(xest.shape[0]//2 - 1):
                x_idx = 2+lm_id*2
                z_idx = 2+lm_id*2+1
                x = xest[x_idx, 0]
                z = xest[z_idx, 0]
                cov_x = pest[x_idx, x_idx]
                cov_z = pest[z_idx, z_idx]
                self.draw_estimate_with_covariance(x, z, cov_x, cov_z, visible_x_range, visible_z_range)
            self.draw_trapezoid(self.vision_trapezoid, self.player_position_gt, visible_x_range, visible_z_range)
            self.image.save(f"slam_simulator_results/images/{self.time:.1f}_{name}.jpg")
            self.image = Image.new(mode="RGB", size=(SCREEN_SIZE["width"], SCREEN_SIZE["width"]), color="white")
            self.draw = ImageDraw.Draw(self.image)


    def draw_trapezoid(self, trapezoid : tuple[Point2d, Point2d, Point2d, Point2d, Point2d], player_position : Point2d,
                       x_range : tuple[float, float], z_range : tuple[float, float]):
        aux_list = []
        for point in trapezoid:
            converted_x = (player_position.x1 + point.x1 - x_range[0])/(x_range[1]-x_range[0])*SCREEN_SIZE["width"]
            converted_z = (player_position.x2 + point.x2 - z_range[0])/(z_range[1]-z_range[0])*SCREEN_SIZE["width"]
            aux_list.extend([converted_x, converted_z])
        self.draw.polygon(aux_list, outline="black", fill=None)

    def draw_position(self, x : float, z : float,
                      x_range : tuple[float, float], z_range : tuple[float, float], player=False):
        if player:
            POINT_RADIUS = 4
        else:
            POINT_RADIUS = 2
        converted_x = (x - x_range[0])/(x_range[1]-x_range[0])*SCREEN_SIZE["width"]
        converted_z = (z - z_range[0])/(z_range[1]-z_range[0])*SCREEN_SIZE["width"]
        if converted_x <= 0 or converted_x >= SCREEN_SIZE["width"]:
            return
        if converted_z <= 0 or converted_z >= SCREEN_SIZE["width"]:
            return
        self.draw.ellipse([converted_x-POINT_RADIUS,converted_z-POINT_RADIUS,
                           converted_x+POINT_RADIUS,converted_z+POINT_RADIUS], 
                           outline="black", fill="black")
        

    def draw_estimate_with_covariance(self, x : float, z : float, cov_x : float, cov_z : float,
                                      x_range : tuple[float, float], z_range : tuple[float, float], player=False):
        if player:
            POINT_RADIUS = 4
        else:
            POINT_RADIUS = 2
        converted_x = (x - x_range[0])/(x_range[1]-x_range[0])*SCREEN_SIZE["width"]
        converted_z = (z - z_range[0])/(z_range[1]-z_range[0])*SCREEN_SIZE["width"]
        if converted_x <= 0 or converted_x >= SCREEN_SIZE["width"]:
            return
        if converted_z <= 0 or converted_z >= SCREEN_SIZE["width"]:
            return
        self.draw.ellipse([converted_x-POINT_RADIUS,converted_z-POINT_RADIUS,
                           converted_x+POINT_RADIUS,converted_z+POINT_RADIUS], 
                           outline="red", fill="red")
        
        cov_x_size = math.sqrt(self.slam.MAHAL_THRESHOLD*cov_x)
        cov_z_size = math.sqrt(self.slam.MAHAL_THRESHOLD*cov_z)
        converted_cov_x = cov_x_size/(x_range[1]-x_range[0])*SCREEN_SIZE["width"]
        converted_cov_z = cov_z_size/(x_range[1]-x_range[0])*SCREEN_SIZE["width"]
        self.draw.ellipse([converted_x-converted_cov_x,converted_z-converted_cov_z,
                           converted_x+converted_cov_x,converted_z+converted_cov_z], 
                           outline="gray", fill=None)


    def run(self):
        while True:
            if not self.step():
                if self.save_images:
                    self.save_state_image()
                break
            if self.save_images:
                self.save_state_image()
