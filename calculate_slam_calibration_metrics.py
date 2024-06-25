import pickle
import time

from tqdm.contrib.itertools import product
import numpy as np
import pandas as pd

from utility.Point2d import Point2d

if __name__ == "__main__":
    u_noise_list = [[4, 4]]
    debug = True

    df_dict = {
        "u_noise": [],
        "player_mse": [],
        "lm_mse": [],
    }

    for u_noise in u_noise_list:
        control_thread_times = np.load(f"slam_calibration/control_thread_times__{str(u_noise[0])}__{str(u_noise[1])}__{debug}.npy")
        modeling_clock_times = np.load(f"slam_calibration/modeling_clock_times__{str(u_noise[0])}__{str(u_noise[1])}__{debug}.npy")
        print("man")
        # expected_trajectory = np.array([[p.x1, p.x2] for p in trajectories[trajectory_name]])
        player_positions_gt = np.load(f"slam_calibration/player_positions_gt__{str(u_noise[0])}__{str(u_noise[1])}__{debug}.npy")
        with open(f"slam_calibration/state_estimate__{str(u_noise[0])}__{str(u_noise[1])}__{debug}.pkl", "rb") as file:
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
        landmarks = np.load(f"slam_calibration/landmark_positions.npy")
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
            
        print(f"\n{total1:.3f} {total2:.3f}")

        if len(min_dists) == 0:
            lm_mse = -1
        else:
            lm_mse = np.array(min_dists).mean()

        df_dict["u_noise"].append(str(u_noise))
        df_dict["player_mse"].append(player_mse)
        df_dict["lm_mse"].append(lm_mse)

    df = pd.DataFrame(data=df_dict)
    df.to_csv("slam_calibration_metrics.csv", index=False)

