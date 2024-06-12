import pickle

from tqdm.contrib.itertools import product
import numpy as np
import pandas as pd

from modeling.SlamSimulator import SlamSimulator
from utility.Point2d import Point2d

if __name__ == "__main__":
    # seed_list = [445]
    seed_list = [445, 727, 10032]
    # num_landmarks_list = [150]
    num_landmarks_list = [0, 3, 20, 50, 150]
    # trajectory_name_list = ["square_1"]
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
    # u_noise_list = [[2, 2]]
    u_noise_list = [[1e-1, 1e-1], [0.5, 0.5], [1, 1], [2, 2]]
    # h_noise_list = [[2.0, 3.0]]
    h_noise_list = [[2.0, 3.0], [20.0, 25.0], [40.0, 50.0]]

    debug = True
    save_images = False

    df_dict = {
        "seed": [],
        "num_landmarks": [],
        "trajectory_name": [],
        "u_noise": [],
        "h_noise": [],
        "correct_match_count": [],
        "wrong_match_count": [],
        "bad_new_creation_count": [],
        "new_object_match_count": [],
    }

    for seed, num_landmarks, trajectory_name, u_noise, h_noise in product(seed_list, num_landmarks_list, trajectory_name_list, u_noise_list, h_noise_list):
        sim = SlamSimulator(seed, num_landmarks, trajectories[trajectory_name], 
                            u_noise, h_noise, debug=debug, save_images=save_images)
        sim.slam.Q = np.diag(u_noise)**2*sim.DT**2
        sim.slam.R = np.diag(h_noise)**2
        sim.run()
        for split_name, times in sim.slam.time_records.items():
            np.save(f"slam_simulator_results/slam_times__{split_name}__{seed}__{num_landmarks}__{trajectory_name}__{str(u_noise[0])}__{str(u_noise[1])}__{str(h_noise[0])}__{str(h_noise[1])}.npy", np.array(times))
        np.save(f"slam_simulator_results/landmark_positions__{seed}__{num_landmarks}.npy", np.array([[p[1].x1, p[1].x2] for p in sim.landmarks]))
        if debug:
            np.save(f"slam_simulator_results/player_positions_gt__{seed}__{num_landmarks}__{trajectory_name}__{str(u_noise[0])}__{str(u_noise[1])}__{str(h_noise[0])}__{str(h_noise[1])}.npy", sim.player_position_gt_list)
            with open(f"slam_simulator_results/state_estimate__{seed}__{num_landmarks}__{trajectory_name}__{str(u_noise[0])}__{str(u_noise[1])}__{str(h_noise[0])}__{str(h_noise[1])}.pkl", "wb") as file:
                pickle.dump(sim.state_estimate_list, file)
            with open(f"slam_simulator_results/covariance_estimate__{seed}__{num_landmarks}__{trajectory_name}__{str(u_noise[0])}__{str(u_noise[1])}__{str(h_noise[0])}__{str(h_noise[1])}.pkl", "wb") as file:
                pickle.dump(sim.covariance_estimate_list, file)
            np.save(f"slam_simulator_results/measurement_errors__{seed}__{num_landmarks}__{trajectory_name}__{str(u_noise[0])}__{str(u_noise[1])}__{str(h_noise[0])}__{str(h_noise[1])}.npy", np.array(sim.measurement_errors))
            np.save(f"slam_simulator_results/measurement_position_errors__{seed}__{num_landmarks}__{trajectory_name}__{str(u_noise[0])}__{str(u_noise[1])}__{str(h_noise[0])}__{str(h_noise[1])}.npy", np.array(sim.measurement_position_errors))
            np.save(f"slam_simulator_results/speed_errors__{seed}__{num_landmarks}__{trajectory_name}__{str(u_noise[0])}__{str(u_noise[1])}__{str(h_noise[0])}__{str(h_noise[1])}.npy", np.array(sim.speed_errors))
            np.save(f"slam_simulator_results/visible_landmarks__{seed}__{num_landmarks}__{trajectory_name}__{str(u_noise[0])}__{str(u_noise[1])}__{str(h_noise[0])}__{str(h_noise[1])}.npy", np.array(sim.visible_landmarks))
            
            df_dict["seed"].append(seed)
            df_dict["num_landmarks"].append(num_landmarks)
            df_dict["trajectory_name"].append(trajectory_name)
            df_dict["u_noise"].append(str(u_noise))
            df_dict["h_noise"].append(str(h_noise))
            df_dict["correct_match_count"].append(sim.slam.correct_match_count)
            df_dict["wrong_match_count"].append(sim.slam.wrong_match_count)
            df_dict["bad_new_creation_count"].append(sim.slam.bad_new_creation_count)
            df_dict["new_object_match_count"].append(sim.slam.new_object_match_count)

    if debug:
        df = pd.DataFrame(data=df_dict)
        df.to_csv("slam_simulator_metrics_2.csv", index=False)
        
    print("done")
