from __future__ import annotations
from typing import TYPE_CHECKING

import math
import time
import os

import numpy as np

from modeling.WorldModel import WorldModel
from modeling.constants import DISTANCE_FOR_OBJECT_SEARCH
if TYPE_CHECKING:
    from modeling.WorldModel import WorldModel


class Slam:
    def __init__(self) -> None:
        # EKF state covariance
        # estimated for 0.1 s
        # self.Q = np.array([[0.1, 0.01937269],
        #     [0.01937269, 0.1]])
        self.Q = np.array([[1000, 0],
            [0, 1000]])
        # Measurement covariance in pixels
        self.R = np.array([
            [3.836410, 0.138089],
            [0.138089, 8.891213]
        ])

        # chi square for 2 DF: 90% 4.605, 95% 5.991, 97.5% 7.378, 99% 9.21
        self.MAHAL_THRESHOLD = 9.21  # Threshold of Mahalanobis distance for data association.
        self.STATE_SIZE = 2  # State size [x,y]
        self.LM_SIZE = 2  # LM state size [x,y]

    # def ekf_slam(self, xEst, PEst, u, z, dt):
    #     """
    #     Performs an iteration of EKF SLAM from the available information.

    #     :param xEst: matrix with player position and landmark position estimates 
    #     :param PEst: the uncertainty in the estimates
    #     :param u: the control function applied to the last position
    #     :param z: measurements at this step
    #     :param dt: delta time
    #     :returns: the next estimated position and associated covariance
    #     """

    #     # Predict
    #     xEst, PEst = self.predict(xEst, PEst, u, dt)

    #     # Update
    #     xEst, PEst = self.update(xEst, PEst, z)

    #     return xEst, PEst

    @staticmethod
    def mahal_dist(p1 : np.ndarray, p2 : np.ndarray, cov : np.ndarray):
        dist = p2 - p1
        return dist.T @ np.linalg.inv(cov) @ dist

    def LM_idx(self, id_):
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
        xEst[0:S] = xEst[0:S] + dt*u
        PEst[0:S, 0:S] = PEst[0:S, 0:S] + self.Q*((dt/0.1)**2) # Q is tuned for 0.1 s
        return xEst, PEst

    def update(self, xEst, PEst, z, conv_z, image_objs, world_model : WorldModel, lm_id_to_object):
        """
        Performs the update step of SLAM

        :param xEst: nx1 state vector after predict step
        :param PEst: nxn covariance matrix after predict step
        :param z: 2*m x 1 vector with measurements, m being number of measurements
        :param conv_z: 2*m x 1 vector with converted measurements, m being number of measurements
        :param image_objs: list with image objects
        :param world_model: world_model
        :param lm_id_to_object: maps slam index to object model
        :returns: the updated state and covariance for the system, plus any added objects
        """
        S = self.STATE_SIZE
        initial_n_LM = (xEst.shape[0] - S) // self.LM_SIZE
        # n_LM will increase if new landmarks are detected
        n_LM = (xEst.shape[0] - S) // self.LM_SIZE
        new_obj_list = []
        # first, associate each observation to a known landmark or create a new one, updating state
        matching_detections, xEst, PEst, n_LM = self.compare_observations_to_state(xEst, PEst, z, conv_z, S, 
                                                                                   initial_n_LM, lm_id_to_object, image_objs, 
                                                                                   new_obj_list, world_model, n_LM)

        # calculate Kalman gain and innovation
        if len(matching_detections) == 0:
            return xEst, PEst, new_obj_list

        xEst, PEst = self.use_matching_detections(xEst, PEst, matching_detections, z, conv_z, S, world_model, n_LM, lm_id_to_object)

        return xEst, PEst, new_obj_list
    
    def compare_observations_to_state(self, xEst, PEst, z, conv_z, S, initial_n_LM, lm_id_to_object, image_objs, new_obj_list, world_model, n_LM):
        matching_detections = {} # map with key being landmark id and value being (idx, distance)
        for iz in range(z.shape[0]//self.LM_SIZE):
            mahal_dists, mahal_id_to_lm_id = self.calculate_mahal_dists(iz, S, initial_n_LM, lm_id_to_object, 
                                                                        image_objs, xEst, conv_z, PEst)
            
            new_object, closest_idx, xEst, PEst, n_LM = self.create_new_object_if_needed(mahal_dists, z, conv_z, iz, S, 
                                                                                         xEst, PEst, new_obj_list, image_objs, 
                                                                                         n_LM, world_model)
            
            self.match_object(new_object, mahal_id_to_lm_id, closest_idx, lm_id_to_object, matching_detections, mahal_dists, iz, world_model, image_objs)
        
        return matching_detections, xEst, PEst, n_LM
    
    def calculate_mahal_dists(self, iz, S, initial_n_LM, lm_id_to_object, image_objs, xEst, conv_z, PEst):
        mahal_dists = []
        iz1 = self.LM_SIZE*iz
        iz2 = self.LM_SIZE*iz+self.LM_SIZE
        # since we're removing objects from the list, mahal index isn't the same as landmark id
        mahal_id_to_lm_id = {}
        for i in range(initial_n_LM):
            # only get objects with same name
            if i in lm_id_to_object and image_objs[iz].id != lm_id_to_object[i].image_id:
                continue
            i1 = self.LM_idx(i)
            i2 = i1+self.LM_SIZE
            dist = (xEst[0:S]+conv_z[iz1:iz2]) - xEst[i1:i2]
            # only get objects within a certain radius
            if (dist[0]**2 + dist[1]**2) > DISTANCE_FOR_OBJECT_SEARCH**2:
                continue
            # get covariance of landmark i
            cov_i = PEst[i1:i2, i1:i2]
            mahal_dist = self.mahal_dist(xEst[0:S]+conv_z[iz1:iz2], xEst[i1:i2], cov_i)
            # mahal_dist = dist.T @ np.linalg.inv(cov_i) @ dist
            mahal_id_to_lm_id[len(mahal_dists)] = i
            mahal_dists.append(mahal_dist)
        
        return mahal_dists, mahal_id_to_lm_id

    def create_new_object_if_needed(self, mahal_dists, z, conv_z, iz, S, xEst, PEst, new_obj_list, image_objs, n_LM, world_model : WorldModel):
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
            new_PEst = np.vstack((np.hstack((PEst, np.zeros((len(xEst), self.LM_SIZE)))),
                            np.hstack((np.zeros((self.LM_SIZE, len(xEst))), initP))))
            xEst = new_xEst
            PEst = new_PEst
            closest_idx = n_LM

            # image_object, slam_state_index, lm_id
            new_obj_list.append((image_objs[iz], S+closest_idx*self.LM_SIZE, closest_idx))

            # update number of landmarks
            n_LM = (xEst.shape[0] - S) // self.LM_SIZE
            new_object = True
        
        return new_object, closest_idx, xEst, PEst, n_LM
    
    def match_object(self, new_object, mahal_id_to_lm_id, closest_idx, lm_id_to_object, matching_detections, mahal_dists, iz, world_model : WorldModel, image_objs):
        if not new_object:
            converted_closest_idx = mahal_id_to_lm_id[closest_idx]
            # if closest_idx not in lm_id_to_object, it means it's matching a new object 
            # and should be ignored 
            if converted_closest_idx not in lm_id_to_object.keys():
                return
            if converted_closest_idx in matching_detections.keys():
                if mahal_dists[closest_idx] < matching_detections[converted_closest_idx][1]:
                    matching_detections[converted_closest_idx] = (iz, mahal_dists[closest_idx])
                else:
                    return
            else:
                matching_detections[converted_closest_idx] = (iz, mahal_dists[closest_idx])
            world_model.matched_object(lm_id_to_object[converted_closest_idx], image_objs[iz])
        

    def use_matching_detections(self, xEst, PEst, matching_detections, z, conv_z, S, world_model, n_LM, lm_id_to_object):
        for converted_closest_idx, detection in matching_detections.items():
            z_matching, conv_z_matching, state_landmark, start, state_observation = self.detections_loop_p1(detection, z, conv_z, S, 
                                                                                                            converted_closest_idx, xEst, world_model)

            H_base = self.detections_loop_p2(world_model, conv_z_matching)

            H, K, innovation = self.detections_loop_p3(H_base, converted_closest_idx, n_LM, PEst, z_matching, state_observation)

            # do update step
            xEst = self.detections_loop_p4(xEst, K, innovation)
            IKH = self.detections_loop_p5(xEst, K, H)
            PEst = self.detections_loop_p6(IKH, PEst)

            self.detections_loop_p7(world_model, lm_id_to_object, converted_closest_idx, xEst, start, state_landmark)
        
        return xEst, PEst
        
    def detections_loop_p1(self, detection, z, conv_z, S, converted_closest_idx, xEst, world_model : WorldModel):
        iz = detection[0]
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
            "use_matching_detections": [],
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
    
    def update(self, xEst, PEst, z, conv_z, image_objs, world_model: WorldModel, lm_id_to_object):
        t1 = time.time_ns()
        return_value = super().update(xEst, PEst, z, conv_z, image_objs, world_model, lm_id_to_object)
        t2 = time.time_ns()
        self.time_records["update"].append([t2-t1])
        return return_value
    
    def compare_observations_to_state(self, xEst, PEst, z, conv_z, S, initial_n_LM, lm_id_to_object, image_objs, new_obj_list, world_model, n_LM):
        t1 = time.time_ns()
        return_value = super().compare_observations_to_state(xEst, PEst, z, conv_z, S, initial_n_LM, lm_id_to_object, image_objs, new_obj_list, world_model, n_LM)
        t2 = time.time_ns()
        self.time_records["compare_observations_to_state"].append([t2-t1])
        return return_value
    
    def calculate_mahal_dists(self, iz, S, initial_n_LM, lm_id_to_object, image_objs, xEst, conv_z, PEst):
        t1 = time.time_ns()
        return_value = super().calculate_mahal_dists(iz, S, initial_n_LM, lm_id_to_object, image_objs, xEst, conv_z, PEst)
        t2 = time.time_ns()
        self.time_records["calculate_mahal_dists"].append([t2-t1])
        return return_value
    
    def create_new_object_if_needed(self, mahal_dists, z, conv_z, iz, S, xEst, PEst, new_obj_list, image_objs, n_LM, world_model):
        t1 = time.time_ns()
        return_value = super().create_new_object_if_needed(mahal_dists, z, conv_z, iz, S, xEst, PEst, new_obj_list, image_objs, n_LM, world_model)
        t2 = time.time_ns()
        self.time_records["create_new_object_if_needed"].append([t2-t1])
        return return_value
    
    def match_object(self, new_object, mahal_id_to_lm_id, closest_idx, lm_id_to_object, matching_detections, mahal_dists, iz, world_model, image_objs):
        t1 = time.time_ns()
        return_value = super().match_object(new_object, mahal_id_to_lm_id, closest_idx, lm_id_to_object, matching_detections, mahal_dists, iz, world_model, image_objs)
        t2 = time.time_ns()
        self.time_records["match_object"].append([t2-t1])
        return return_value
    
    def use_matching_detections(self, xEst, PEst, matching_detections, z, conv_z, S, world_model, n_LM, lm_id_to_object):
        t1 = time.time_ns()
        return_value = super().use_matching_detections(xEst, PEst, matching_detections, z, conv_z, S, world_model, n_LM, lm_id_to_object)
        t2 = time.time_ns()
        self.time_records["use_matching_detections"].append([t2-t1])
        return return_value
    
    def detections_loop_p1(self, detection, z, conv_z, S, converted_closest_idx, xEst, world_model):
        t1 = time.time_ns()
        return_value = super().detections_loop_p1(detection, z, conv_z, S, converted_closest_idx, xEst, world_model)
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
