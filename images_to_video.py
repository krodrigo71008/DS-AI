import cv2
import os

import tqdm

# taken from https://stackoverflow.com/questions/44947505/how-to-make-a-movie-out-of-images-in-python

image_folder = 'decision_making_simulator_results'
video_name = 'decision_making_simulator_results.mp4'
image_format = '.png'

images = [img for img in os.listdir(image_folder) if img.endswith(image_format)]
frame = cv2.imread(os.path.join(image_folder, images[0]))
height, width, layers = frame.shape

# example of name: '10.3_c_after_update.jpg'
def slam_sim_value_function(name):
    return (float(name.split('_')[0]), name.split('_')[1])

# example of name: '10.3.png'
def decision_making_sim_value_function(name):
    return float(name[:-4])

# images = sorted(images, key=slam_sim_value_function)
images = sorted(images, key=decision_making_sim_value_function)

video = cv2.VideoWriter(video_name, cv2.VideoWriter_fourcc(*'mp4v'), 10, (width, height))

for image in tqdm.tqdm(images):
    video.write(cv2.imread(os.path.join(image_folder, image)))

cv2.destroyAllWindows()
video.release()