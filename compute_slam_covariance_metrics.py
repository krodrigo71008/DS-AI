from itertools import product
import numpy as np

from modeling.SlamSimulator import SlamSimulator
from utility.Point2d import Point2d

if __name__ == "__main__":
    seed_list = [445]
    # seed_list = [445, 727, 10032]
    num_landmarks_list = [150]
    # num_landmarks_list = [0, 3, 20, 50, 150]
    trajectory_name_list = ["square_1"]
    # trajectory_name_list = ["square_1", "square_2", "spiral_1", "spiral_2"]
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
    u_noise_list = [[2, 2]]
    # u_noise_list = [[1e-1, 1e-1], [0.5, 0.5], [1, 1], [2, 2]]
    h_noise_list = [[2.0, 3.0]]
    # h_noise_list = [[2.0, 3.0], [20.0, 25.0], [40.0, 50.0]]

    debug = False
    save_images = False

    NUM_SIMS = 1000

    for seed, num_landmarks, trajectory_name, u_noise, h_noise in product(seed_list, num_landmarks_list, trajectory_name_list, u_noise_list, h_noise_list):
        sims : list[SlamSimulator] = []
        landmarks : list[tuple[int, Point2d]] = None
        for _ in range(NUM_SIMS):
            sim = SlamSimulator(seed, num_landmarks, trajectories[trajectory_name], 
                                u_noise, h_noise, debug=debug, save_images=save_images, randomize=True, closed_control_loop=False)
            if landmarks is None:
                landmarks = sim.landmarks
            else:
                sim.landmarks = landmarks
            sim.slam.Q = np.diag(u_noise)**2*sim.DT**2
            sim.slam.R = np.diag(h_noise)**2
            sims.append(sim)
        
        cos_sim_log = []
        norm_dist_log = []
        while True:
            should_break = False
            player_positions = []
            landmark_estimates = {}
            for _, lm in landmarks:
                landmark_estimates[lm] = []

            for sim in sims:
                return_value = sim.step()
                if not return_value:
                    should_break = True

                player_positions.append([sim.player_position_gt.x1, sim.player_position_gt.x2])
                for i, lm in sim.slam._state_landmark_gt.items():
                    landmark_estimates[lm].append([sim.xEst[sim.slam.STATE_SIZE+i*sim.slam.LM_SIZE, 0], 
                                                   sim.xEst[sim.slam.STATE_SIZE+i*sim.slam.LM_SIZE+1, 0]])

            player_simulated_cov = np.cov(np.array(player_positions).T)

            lm_cov = {}
            for lm, pos_list in landmark_estimates.items():
                if len(pos_list) > 1:
                    lm_cov[lm] = np.cov(np.array(pos_list).T)

            player_cov_cos_sim_list = []
            player_cov_norm_dist_list = []
            for sim in sims:
                v1 = sim.PEst[0:2, 0:2].flatten()
                v2 = player_simulated_cov.flatten()
                v1_norm = np.linalg.norm(v1)
                v2_norm = np.linalg.norm(v2)
                cos_sim = (v1*v2).sum()/v1_norm/v2_norm
                norm_dist = np.abs(v1_norm - v2_norm)
                player_cov_cos_sim_list.append(cos_sim)
                player_cov_norm_dist_list.append(norm_dist)

            lm_cov_cos_sim_lists = {}
            lm_cov_norm_dist_lists = {}

            for sim in sims:
                n_LM = (sim.xEst.shape[0]-sim.slam.STATE_SIZE)//sim.slam.LM_SIZE
                for i in range(n_LM):
                    if sim.slam._state_landmark_gt[i] not in lm_cov.keys():
                        # this only happens when there's only one simulation in which the lm was in the slam state, so there is no covariance
                        continue
                    state_idx = sim.slam.STATE_SIZE+i*sim.slam.LM_SIZE
                    v1 = sim.PEst[state_idx:state_idx+2, state_idx:state_idx+2].flatten()
                    v2 = lm_cov[sim.slam._state_landmark_gt[i]].flatten()
                    v1_norm = np.linalg.norm(v1)
                    v2_norm = np.linalg.norm(v2)
                    cos_sim = (v1*v2).sum()/v1_norm/v2_norm
                    norm_dist = np.abs(v1_norm - v2_norm)
                    if sim.slam._state_landmark_gt[i] in lm_cov_cos_sim_lists.keys():
                        lm_cov_cos_sim_lists[sim.slam._state_landmark_gt[i]].append(cos_sim)
                    else:
                        lm_cov_cos_sim_lists[sim.slam._state_landmark_gt[i]] = [cos_sim]
                    if sim.slam._state_landmark_gt[i] in lm_cov_norm_dist_lists.keys():
                        lm_cov_norm_dist_lists[sim.slam._state_landmark_gt[i]].append(norm_dist)
                    else:
                        lm_cov_norm_dist_lists[sim.slam._state_landmark_gt[i]] = [norm_dist]

            avg_player_cos_sim = np.mean(player_cov_cos_sim_list)
            avg_player_norm_dist = np.mean(player_cov_norm_dist_list)

            lm_cov_cos_sim_list = [np.mean(list_) for list_ in lm_cov_cos_sim_lists.values()]
            lm_cov_norm_dist_list = [np.mean(list_) for list_ in lm_cov_norm_dist_lists.values()]
            avg_lm_cos_sim = np.mean(lm_cov_cos_sim_list)
            avg_lm_norm_dist = np.mean(lm_cov_norm_dist_list)

            cos_sim_log.append(avg_lm_cos_sim)
            norm_dist_log.append(avg_lm_norm_dist)

            print(f"{sim.time:.1f}/{sim.turn_times[-1]:.1f}")

            if should_break:
                break
        
        np.save(f"slam_simulator_results/slam_covariance_cosine_similarity__{seed}__{num_landmarks}__{trajectory_name}__{str(u_noise[0])}__{str(u_noise[1])}__{str(h_noise[0])}__{str(h_noise[1])}.npy", np.array(cos_sim_log))
        np.save(f"slam_simulator_results/slam_covariance_norm_distance__{seed}__{num_landmarks}__{trajectory_name}__{str(u_noise[0])}__{str(u_noise[1])}__{str(h_noise[0])}__{str(h_noise[1])}.npy", np.array(norm_dist_log))
        
    print("done")
