from __future__ import annotations
from typing import TYPE_CHECKING

import math
import time
import os

import numpy as np

from modeling.WorldModel import WorldModel
from modeling.constants import DISTANCE_FOR_OBJECT_SEARCH, BASE_CONTROL_DT
if TYPE_CHECKING:
    from modeling.WorldModel import WorldModel
    from utility.Point2d import Point2d


class Slam:
    def __init__(self, debug=False) -> None:
        # EKF state covariance
        # estimated for 0.1 s
        # self.Q = np.array([[0.1, 0.01937269],
        #     [0.01937269, 0.1]])
        self.Q = np.array([[4, 0],
            [0, 4]])
        # Measurement covariance in pixels
        self.R = np.array([
            [436.410, 0],
            [0, 989.1213]
        ])

        # chi square for 2 DF: 90% 4.605, 95% 5.991, 97.5% 7.378, 99% 9.21
        self.MAHAL_THRESHOLD = 9.21  # Threshold of Mahalanobis distance for data association.
        self.STATE_SIZE = 2  # State size [x,y]
        self.LM_SIZE = 2  # LM state size [x,y]

        self.debug = debug
        if debug:
            self.filtered_observations = None

        # this is updated when we match an object to a new landmark, that is, two detections are so close that they point
        # to the same object, this should never happen since we only calculate mahal dists for 
        # previously existing objects, but you never know
        self.new_object_match_count = 0
        # this is only used with the simulator for debugging purposes
        # maps lm state id to its gt xz coordinates
        self._state_landmark_gt : dict[int, Point2d] = {}
        self.bad_new_creation_count = 0
        self.wrong_match_count = 0
        self.correct_match_count = 0

    @staticmethod
    def mahal_dist(p1 : np.ndarray, p2 : np.ndarray, cov : np.ndarray) -> float:
        """Calculates mahalanobis distance between p1 and p2 given covariance matrix cov

        :param p1: p1
        :type p1: np.ndarray
        :param p2: p2
        :type p2: np.ndarray
        :param cov: covariance matrix
        :type cov: np.ndarray
        :return: mahalanobis distance
        :rtype: float
        """
        dist = p2 - p1
        res = dist.T @ np.linalg.inv(cov) @ dist
        return res[0, 0]

    def LM_idx(self, id_: int) -> int:
        """Convert landmark id to state index

        :param id_: landmark id
        :type id_: int
        :return: state index
        :rtype: int
        """
        return self.STATE_SIZE + id_*self.LM_SIZE

    def predict(self, xEst, PEst, u, dt):
        """
        Performs the prediction step of SLAM

        :param xEst: nx1 state vector
        :param PEst: nxn covariance matrix
        :param u: 2x1 control vector
        :param dt: delta time
        :returns: predicted state vector, predicted covariance
        """
        S = self.STATE_SIZE
        # if we're not moving, no need to update matrices
        if u[0, 0] == 0.0 and u[1, 0] == 0.0:
            return xEst, PEst
        xEst[0:S] = xEst[0:S] + dt*u
        PEst[0:S, 0:S] = PEst[0:S, 0:S] + self.Q*((dt/BASE_CONTROL_DT)**2) # Q is tuned for 0.1 s
        return xEst, PEst

    def update(self, xEst, PEst, z, conv_z, image_objs, world_model : WorldModel, lm_id_to_object, lm_points : list[Point2d] = None):
        """
        Performs the update step of SLAM

        :param xEst: nx1 state vector after predict step
        :param PEst: nxn covariance matrix after predict step
        :param z: 2*m x 1 vector with measurements, m being number of measurements
        :param conv_z: 2*m x 1 vector with converted measurements, m being number of measurements
        :param image_objs: list with image objects
        :param world_model: world_model
        :param lm_id_to_object: maps slam index to object model
        :param lm_points: points with ground truth xz points for observations (only used with simulator)
        :returns: the updated state and covariance for the system, plus any added objects
        """
        S = self.STATE_SIZE
        initial_n_LM = (xEst.shape[0] - S) // self.LM_SIZE
        # n_LM will increase if new landmarks are detected
        n_LM = (xEst.shape[0] - S) // self.LM_SIZE
        new_obj_list = []
        for iz in range(z.shape[0]//self.LM_SIZE):
            # first, associate each observation to a known landmark or create a new one, updating state
            matching_detection, xEst, PEst, n_LM = self.compare_observations_to_state(xEst, PEst, z, conv_z, iz, S, 
                                                                                    initial_n_LM, lm_id_to_object, image_objs, 
                                                                                    new_obj_list, world_model, n_LM, lm_points)

            # calculate Kalman gain and innovation
            if matching_detection is None:
                continue

            xEst, PEst = self.use_matching_detection(xEst, PEst, matching_detection, z, conv_z, S, world_model, n_LM, lm_id_to_object)

        return xEst, PEst, new_obj_list
    
    def compare_observations_to_state(self, xEst, PEst, z, conv_z, iz, S, 
                                      initial_n_LM, lm_id_to_object, image_objs, 
                                      new_obj_list, world_model, n_LM, lm_points):
        """Calculate mahal dists, create new object and match object"""
        mahal_dists, mahal_id_to_lm_id = self.calculate_mahal_dists(z, conv_z, iz, S, initial_n_LM, lm_id_to_object, 
                                                                    image_objs, xEst, PEst, world_model)
        
        new_object, closest_idx, xEst, PEst, n_LM = self.create_new_object_if_needed(mahal_dists, z, conv_z, iz, S, 
                                                                                        xEst, PEst, new_obj_list, image_objs, 
                                                                                        n_LM, world_model, lm_points)
        
        matching_detection = self.match_object(new_object, mahal_id_to_lm_id, 
                                               closest_idx, lm_id_to_object, 
                                               iz, world_model, image_objs, lm_points)
        
        return matching_detection, xEst, PEst, n_LM
    
    def calculate_mahal_dists(self, z, conv_z, iz, S, initial_n_LM, lm_id_to_object, image_objs, xEst, PEst, 
                              world_model : WorldModel):
        mahal_dists = []
        iz1 = self.LM_SIZE*iz
        iz2 = self.LM_SIZE*iz+self.LM_SIZE
        conversion_jacob = world_model.jacob_inverseH(z[iz1, 0], z[iz1+1, 0])
        # since we're removing objects from the list, mahal index isn't the same as landmark id
        mahal_id_to_lm_id = {}
        if self.debug:
            self.filtered_observations = []
        for i in range(initial_n_LM):
            # only get objects with same name
            if i < len(lm_id_to_object) and image_objs[iz].id != lm_id_to_object[i].image_id:
                if self.debug:
                    self.filtered_observations.append(i)
                continue
            i1 = self.LM_idx(i)
            i2 = i1+self.LM_SIZE
            # player position + local object position compared to object position in state
            dist = (xEst[0:S]+conv_z[iz1:iz2]) - xEst[i1:i2]
            # only get objects within a certain radius
            if (dist[0, 0]**2 + dist[1, 0]**2) > DISTANCE_FOR_OBJECT_SEARCH**2:
                if self.debug:
                    self.filtered_observations.append(i)
                continue
            # covariance of landmark i + player covariance + covariance of observation
            cov_i = PEst[i1:i2, i1:i2] + PEst[0:S, 0:S] + conversion_jacob @ self.R @ conversion_jacob.T
            mahal_dist = self.mahal_dist(xEst[0:S]+conv_z[iz1:iz2], xEst[i1:i2], cov_i)
            # mahal_dist = dist.T @ np.linalg.inv(cov_i) @ dist
            mahal_id_to_lm_id[len(mahal_dists)] = i
            mahal_dists.append(mahal_dist)
        
        if self.debug:
            assert len(mahal_id_to_lm_id) == len(mahal_dists)
            assert len(self.filtered_observations) + len(mahal_id_to_lm_id) == initial_n_LM
            # prev_v = -1
            # for k, v in mahal_id_to_lm_id.items():
            #     for i in range(prev_v+1, v):
            #         assert i in self.filtered_observations

            #     # calculate cov again to confirm mahal_id_to_lm_id is correct
            #     cov_i = PEst[S+2*v:S+2*v+2, S+2*v:S+2*v+2] + PEst[0:S,0:S] + conversion_jacob @ self.R @ conversion_jacob.T
            #     mahal_dist = self.mahal_dist(xEst[0:S]+conv_z[iz1:iz2], xEst[S+2*v:S+2*v+2], cov_i)
            #     assert mahal_dist == mahal_dists[k]

            #     prev_v = v

            # for i in range(prev_v+1, initial_n_LM):
            #     assert i in self.filtered_observations

        return mahal_dists, mahal_id_to_lm_id

    def create_new_object_if_needed(self, mahal_dists, z, conv_z, iz, S, xEst, PEst, new_obj_list, image_objs, n_LM, world_model : WorldModel, lm_points):
        iz1 = self.LM_SIZE*iz
        iz2 = self.LM_SIZE*iz+self.LM_SIZE
        if len(mahal_dists) > 0:
            closest_idx = np.argmin(mahal_dists)
        new_object = False
        if len(mahal_dists) == 0 or mahal_dists[closest_idx] > self.MAHAL_THRESHOLD:
            # new landmark
            # initial covariance is equal to our position's covariance + observation covariance
            conversion_jacob = world_model.jacob_inverseH(z[iz1, 0], z[iz1+1, 0])
            initP = PEst[0:S, 0:S] + conversion_jacob @ self.R @ conversion_jacob.T
            new_xEst = np.vstack((xEst, xEst[0:S]+conv_z[iz1:iz2]))
            # TEMPORARY HORRIBLE NASTY HACK
            new_PEst = np.vstack((np.hstack((PEst, np.zeros((len(xEst), self.LM_SIZE)))),
                            np.hstack((np.zeros((self.LM_SIZE, len(xEst))), initP))))
            # new_PEst = np.vstack((np.hstack((PEst, np.tile((initP+PEst[0:S, 0:S])/2, (len(xEst)//self.LM_SIZE, 1)))),
            #                 np.hstack((np.tile((initP+PEst[0:S, 0:S])/2, len(xEst)//self.LM_SIZE), initP))))
            xEst = new_xEst
            PEst = new_PEst
            closest_idx = n_LM

            # image_object, slam_state_index, lm_id
            new_obj_list.append((image_objs[iz], S+closest_idx*self.LM_SIZE, closest_idx))

            # update number of landmarks
            n_LM = (xEst.shape[0] - S) // self.LM_SIZE
            new_object = True

            if lm_points is not None:
                # if the landmark is one of the landmarks in the state, this means this landmark shouldn't have been created
                # cause it was in the state, but the matching failed
                if lm_points[iz] in self._state_landmark_gt.values():
                    self.bad_new_creation_count += 1
                self._state_landmark_gt[n_LM-1] = lm_points[iz]

        return new_object, closest_idx, xEst, PEst, n_LM
    
    def match_object(self, new_object, mahal_id_to_lm_id, closest_idx, 
                     lm_id_to_object, iz, world_model : WorldModel, image_objs, lm_points):
        matching_detection = None
        if not new_object:
            converted_closest_idx = mahal_id_to_lm_id[closest_idx]
            # if closest_idx not in lm_id_to_object, it means it's matching a new object 
            # and should be ignored
            if converted_closest_idx >= len(lm_id_to_object):
                self.new_object_match_count += 1
                return
            matching_detection = (converted_closest_idx, iz)
            world_model.matched_object(lm_id_to_object[converted_closest_idx], image_objs[iz])
            if lm_points is not None:
                if self._state_landmark_gt[converted_closest_idx] == lm_points[iz]:
                    self.correct_match_count += 1
                else:
                    self.wrong_match_count += 1
        return matching_detection
        

    def use_matching_detection(self, xEst, PEst, matching_detection, z, conv_z, S, world_model, n_LM, lm_id_to_object):
        converted_closest_idx, iz = matching_detection
        z_matching, conv_z_matching, state_landmark, start, state_observation = self.detections_loop_p1(z, conv_z, iz, S, 
                                                                                                        converted_closest_idx, xEst, world_model)

        H_base = self.detections_loop_p2(world_model, conv_z_matching)

        H, K, innovation = self.detections_loop_p3(H_base, converted_closest_idx, n_LM, PEst, z_matching, state_observation)

        # do update step
        xEst = self.detections_loop_p4(xEst, K, innovation)
        IKH = self.detections_loop_p5(xEst, K, H)
        PEst = self.detections_loop_p6(IKH, PEst)

        # self.detections_loop_p7(world_model, lm_id_to_object, converted_closest_idx, xEst, start, state_landmark)
        
        return xEst, PEst
        
    def detections_loop_p1(self, z, conv_z, iz, S, converted_closest_idx, xEst, world_model : WorldModel):
        z_matching = z[iz*self.LM_SIZE:(iz+1)*self.LM_SIZE]
        conv_z_matching = conv_z[iz*self.LM_SIZE:(iz+1)*self.LM_SIZE]
        
        start = S + converted_closest_idx*self.LM_SIZE

        state_landmark = xEst[start:start+self.LM_SIZE].copy()

        state_observation = world_model.H_function(state_landmark[0, 0] - xEst[0, 0], state_landmark[1, 0] - xEst[1, 0])
        state_observation = np.array([[state_observation[0], state_observation[1]]]).T
        
        return z_matching, conv_z_matching, state_landmark, start, state_observation
    
    def detections_loop_p2(self, world_model : WorldModel, conv_z_matching):
        # we have to pass landmark positions relative to the player, not in the global coordinate system
        H_base = world_model.jacobH(conv_z_matching[0, 0], conv_z_matching[1, 0])
        return np.array(H_base)

    def detections_loop_p3(self, H_base, converted_closest_idx, n_LM, PEst, z_matching, state_observation):
        H = np.hstack((-H_base, 
                        np.zeros((2, converted_closest_idx*self.LM_SIZE)), 
                        H_base, 
                        np.zeros((2, (n_LM-converted_closest_idx-1)*self.LM_SIZE))))

        K = PEst @ H.T @ np.linalg.inv(H @ PEst @ H.T + self.R)
        innovation = z_matching - state_observation
        return H, K, innovation

    def detections_loop_p4(self, xEst, K, innovation):
        xEst = xEst + K @ innovation
        return xEst

    def detections_loop_p5(self, xEst, K, H):
        IKH = np.eye(xEst.shape[0]) - K @ H
        return IKH

    def detections_loop_p6(self, IKH, PEst):
        PEst = IKH @ PEst
        return PEst
        
    def detections_loop_p7(self, world_model : WorldModel, lm_id_to_object, converted_closest_idx, xEst, start, state_landmark):
        world_model.recheck_object_chunk(lm_id_to_object[converted_closest_idx], 
                                        xEst[start:start+self.LM_SIZE, 0], 
                                        (state_landmark[0, 0], state_landmark[1, 0]))

class SlamTimer(Slam):
    def __init__(self) -> None:
        super().__init__()
        self.time_records = {
            "predict": [],
            "update": [],
            "compare_observations_to_state": [],
            "calculate_mahal_dists": [],
            "create_new_object_if_needed": [],
            "match_object": [],
            "use_matching_detection": [],
            "detections_loop_p1": [],
            "detections_loop_p2": [],
            "detections_loop_p3": [],
            "detections_loop_p4": [],
            "detections_loop_p5": [],
            "detections_loop_p6": [],
            "detections_loop_p7": [],
        }

    def predict(self, xEst, PEst, u, dt):
        t1 = time.time_ns()
        return_value = super().predict(xEst, PEst, u, dt)
        t2 = time.time_ns()
        self.time_records["predict"].append([t2-t1])
        return return_value
    
    def update(self, xEst, PEst, z, conv_z, image_objs, world_model: WorldModel, lm_id_to_object, lm_points : list[Point2d]):
        t1 = time.time_ns()
        return_value = super().update(xEst, PEst, z, conv_z, image_objs, world_model, lm_id_to_object, lm_points)
        t2 = time.time_ns()
        self.time_records["update"].append([t2-t1])
        return return_value
    
    def compare_observations_to_state(self, xEst, PEst, z, conv_z, iz, S, 
                                      initial_n_LM, lm_id_to_object, image_objs, 
                                      new_obj_list, world_model, n_LM, lm_points):
        t1 = time.time_ns()
        return_value = super().compare_observations_to_state(xEst, PEst, z, conv_z, iz, S, 
                                                             initial_n_LM, lm_id_to_object, image_objs, 
                                                             new_obj_list, world_model, n_LM, lm_points)
        t2 = time.time_ns()
        self.time_records["compare_observations_to_state"].append([t2-t1])
        return return_value
    
    def calculate_mahal_dists(self, z, conv_z, iz, S, initial_n_LM, lm_id_to_object, image_objs, xEst, PEst, 
                              world_model : WorldModel):
        t1 = time.time_ns()
        return_value = super().calculate_mahal_dists(z, conv_z, iz, S, initial_n_LM, lm_id_to_object, image_objs, xEst, PEst, world_model)
        t2 = time.time_ns()
        self.time_records["calculate_mahal_dists"].append([t2-t1])
        return return_value
    
    def create_new_object_if_needed(self, mahal_dists, z, conv_z, iz, S, xEst, PEst, new_obj_list, image_objs, n_LM, world_model, lm_points):
        t1 = time.time_ns()
        return_value = super().create_new_object_if_needed(mahal_dists, z, conv_z, iz, S, xEst, PEst, new_obj_list, image_objs, n_LM, world_model, lm_points)
        t2 = time.time_ns()
        self.time_records["create_new_object_if_needed"].append([t2-t1])
        return return_value
    
    def match_object(self, new_object, mahal_id_to_lm_id, closest_idx, lm_id_to_object, 
                     iz, world_model, image_objs, lm_points):
        t1 = time.time_ns()
        return_value = super().match_object(new_object, mahal_id_to_lm_id, closest_idx, lm_id_to_object, 
                                            iz, world_model, image_objs, lm_points)
        t2 = time.time_ns()
        self.time_records["match_object"].append([t2-t1])
        return return_value
    
    def use_matching_detection(self, xEst, PEst, matching_detection, z, conv_z, S, world_model, n_LM, lm_id_to_object):
        t1 = time.time_ns()
        return_value = super().use_matching_detection(xEst, PEst, matching_detection, z, conv_z, S, world_model, n_LM, lm_id_to_object)
        t2 = time.time_ns()
        self.time_records["use_matching_detection"].append([t2-t1])
        return return_value
    
    def detections_loop_p1(self, z, conv_z, iz, S, converted_closest_idx, xEst, world_model):
        t1 = time.time_ns()
        return_value = super().detections_loop_p1(z, conv_z, iz, S, converted_closest_idx, xEst, world_model)
        t2 = time.time_ns()
        self.time_records["detections_loop_p1"].append([t2-t1])
        return return_value
    
    def detections_loop_p2(self, world_model, conv_z_matching):
        t1 = time.time_ns()
        return_value = super().detections_loop_p2(world_model, conv_z_matching)
        t2 = time.time_ns()
        self.time_records["detections_loop_p2"].append([t2-t1])
        return return_value
    
    def detections_loop_p3(self, H_base, converted_closest_idx, n_LM, PEst, z_matching, state_observation):
        t1 = time.time_ns()
        return_value = super().detections_loop_p3(H_base, converted_closest_idx, n_LM, PEst, z_matching, state_observation)
        t2 = time.time_ns()
        self.time_records["detections_loop_p3"].append([t2-t1])
        return return_value
    
    def detections_loop_p4(self, xEst, K, innovation):
        t1 = time.time_ns()
        return_value = super().detections_loop_p4(xEst, K, innovation)
        t2 = time.time_ns()
        self.time_records["detections_loop_p4"].append([t2-t1])
        return return_value
    
    def detections_loop_p5(self, xEst, K, H):
        t1 = time.time_ns()
        return_value = super().detections_loop_p5(xEst, K, H)
        t2 = time.time_ns()
        self.time_records["detections_loop_p5"].append([t2-t1])
        return return_value
    
    def detections_loop_p6(self, IKH, PEst):
        t1 = time.time_ns()
        return_value = super().detections_loop_p6(IKH, PEst)
        t2 = time.time_ns()
        self.time_records["detections_loop_p6"].append([t2-t1])
        return return_value
    
    def detections_loop_p7(self, world_model, lm_id_to_object, converted_closest_idx, xEst, start, state_landmark):
        t1 = time.time_ns()
        return_value = super().detections_loop_p7(world_model, lm_id_to_object, converted_closest_idx, xEst, start, state_landmark)
        t2 = time.time_ns()
        self.time_records["detections_loop_p7"].append([t2-t1])
        return return_value

    # def detections_loop_p4(self, xEst, K, innovation, H, PEst):
    #     t1 = time.time_ns()
    #     return_value = super().detections_loop_p4(xEst, K, innovation, H, PEst)
    #     t2 = time.time_ns()
    #     self.time_records["detections_loop_p4"].append([t2-t1])
    #     return return_value
    
    # def detections_loop_p5(self, world_model, lm_id_to_object, converted_closest_idx, xEst, start, state_landmark):
    #     t1 = time.time_ns()
    #     return_value = super().detections_loop_p5(world_model, lm_id_to_object, converted_closest_idx, xEst, start, state_landmark)
    #     t2 = time.time_ns()
    #     self.time_records["detections_loop_p5"].append([t2-t1])
    #     return return_value
