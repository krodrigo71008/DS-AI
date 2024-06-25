import pickle
import time

from tqdm.contrib.itertools import product
import numpy as np
import pandas as pd

from utility.Point2d import Point2d

seed_list = [445, 727, 10032]
num_landmarks_list = [0, 3, 20, 50, 150]
trajectory_name_list = ["square_1", "square_2", "spiral_1", "spiral_2"]
trajectories = {
    "square_1" : [Point2d(50, 50), Point2d(50, -50), Point2d(-50, -50), Point2d(-50, 50), Point2d(50, 50), Point2d(0, 0)],
    "square_2" : [Point2d(0, 50), Point2d(50, 0), Point2d(0, -50), Point2d(-50, 0), Point2d(0, 50), Point2d(0, 0)],
    "spiral_1" : [Point2d(0, 20), Point2d(20, 20), Point2d(20, -40), Point2d(-40, -40), 
                    Point2d(-40, 60), Point2d(60, 60), Point2d(60, -80), Point2d(-80, -80)],
    "spiral_2" : [Point2d(1, 1), Point2d(3, -1), Point2d(3, -4), Point2d(0, -5), Point2d(-3, -3), Point2d(-5, 0), Point2d(-3, 5),  
                Point2d(0, 8), Point2d(5, 8), Point2d(10, 4), Point2d(14, -4), Point2d(10, -10), Point2d(1, -14), Point2d(-12, -9),  
                Point2d(-16, 3), Point2d(-10, 14), Point2d(-1, 23), Point2d(13, 20), Point2d(24, 7), Point2d(27, -6), Point2d(17, -18),  
                Point2d(2, -28), Point2d(-15, -25), Point2d(-31, -6), Point2d(-26, 17), Point2d(-11, 34), Point2d(14, 35), Point2d(32, 21),  
                Point2d(41, 0), Point2d(29, -28), Point2d(11, -41), Point2d(-21, -44), Point2d(-41, -31)],
}
u_noise_list = [[1e-1, 1e-1], [0.5, 0.5], [1, 1], [2, 2]]
h_noise_list = [[2.0, 3.0], [20.0, 25.0], [40.0, 50.0]]

df_dict = {
    "seed": [],
    "num_landmarks": [],
    "trajectory_name": [],
    "u_noise": [],
    "h_noise": [],
    "player_mse": [],
    "lm_mse": [],
}

for seed, num_landmarks, trajectory_name, u_noise, h_noise in product(seed_list, num_landmarks_list, trajectory_name_list, u_noise_list, h_noise_list):
    # expected_trajectory = np.array([[p.x1, p.x2] for p in trajectories[trajectory_name]])
    player_positions_gt = np.load(f"slam_simulator_results/player_positions_gt__{seed}__{num_landmarks}__{trajectory_name}__{str(u_noise[0])}__{str(u_noise[1])}__{str(h_noise[0])}__{str(h_noise[1])}.npy")
    with open(f"slam_simulator_results/state_estimate__{seed}__{num_landmarks}__{trajectory_name}__{str(u_noise[0])}__{str(u_noise[1])}__{str(h_noise[0])}__{str(h_noise[1])}.pkl", "rb") as file:
        state_list = pickle.load(file)
    temp_list = []
    for state in state_list:
        temp_list.append([state[0, 0], state[1, 0]])
    player_positions_estimate = np.array(temp_list)
    assert player_positions_gt.shape == player_positions_estimate.shape
    x1_diff = (player_positions_gt - player_positions_estimate)[:, 0]
    x2_diff = (player_positions_gt - player_positions_estimate)[:, 1]
    player_mse = (x1_diff**2 + x2_diff**2).mean()
    min_dists = []
    landmarks = np.load(f"slam_simulator_results/landmark_positions__{seed}__{num_landmarks}.npy")
    # state_correspondence[i] = j means LM i in state maps to landmarks[j, :]
    state_correspondence = {}
    latest_n_LM = -1
    total1 = 0
    total2 = 0
    for state in state_list:
        n_LM = (state.shape[0] - 2) // 2
        if n_LM > 0:
            # check if we need to recompute state_correspondence
            if latest_n_LM != n_LM:
                t1 = time.time_ns()
                for i in range(n_LM):
                    start = 2+i*2
                    est_lm_pos = state[start:start+2, 0]
                    # IMPORTANT: I'm assuming state only ever grows and no landmarks are ever erased from state
                    if i in state_correspondence:
                        lm_i = state_correspondence[i]
                        lm = landmarks[lm_i, :].T
                        min_dist = ((lm - est_lm_pos)**2).sum()
                    else:
                        min_dist = -1
                        for lm_i in range(landmarks.shape[0]):
                            lm = landmarks[lm_i, :].T
                            if min_dist == -1 or ((lm - est_lm_pos)**2).sum() < min_dist:
                                min_dist = ((lm - est_lm_pos)**2).sum()
                                state_correspondence[i] = lm_i
                    min_dists.append(min_dist)
                t2 = time.time_ns()
                total1 += (t2-t1)/1e6
            else:
                t1 = time.time_ns()
                temp_min_dists = []
                for i in range(n_LM):
                    start = 2+i*2
                    est_lm_pos = state[start:start+2, 0]
                    lm_i = state_correspondence[i]
                    lm = landmarks[lm_i, :].T
                    dist = ((lm - est_lm_pos)**2).sum()
                    temp_min_dists.append(dist)
                t2 = time.time_ns() 
                total2 += (t2-t1)/1e6
                
        latest_n_LM = n_LM
        
    # print(f"\n{total1:.3f} {total2:.3f}")

    if len(min_dists) == 0:
        lm_mse = -1
    else:
        lm_mse = np.array(min_dists).mean()

    df_dict["seed"].append(seed)
    df_dict["num_landmarks"].append(num_landmarks)
    df_dict["trajectory_name"].append(trajectory_name)
    df_dict["u_noise"].append(str(u_noise))
    df_dict["h_noise"].append(str(h_noise))
    df_dict["player_mse"].append(player_mse)
    df_dict["lm_mse"].append(lm_mse)

df = pd.DataFrame(data=df_dict)
df.to_csv("slam_simulator_metrics.csv", index=False)

