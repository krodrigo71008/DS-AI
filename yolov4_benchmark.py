import cv2
import time
import os
import glob

from perception.Perception import Perception
from utility.utility import draw_annotations

# images_dir = '../darknet-master/data/obj'
# images_dir = 'augmentation'
images_dir = 'perception/images'
text_logs_dir = 'perception/text_logs'
predictions_dir = 'perception/predictions'

perception = Perception()

NUM_IMAGES = 107


if not os.path.exists(text_logs_dir):
    os.makedirs(text_logs_dir)

old_text_logs = glob.glob(text_logs_dir + '/*.txt')
for f in old_text_logs:
    os.remove(f)

if not os.path.exists(predictions_dir):
    os.makedirs(predictions_dir)

old_predictions = glob.glob(predictions_dir + '/*.jpg')
for f in old_predictions:
    os.remove(f)


filenames = glob.glob(images_dir + '/**/*.jpg', recursive=True)
filenames.extend(glob.glob(images_dir + '/**/*.png', recursive=True))

# images_file = '../darknet-master/data/train.txt'
# with open(images_file) as f:
#     filenames = ['../darknet-master/' + fname.strip() for fname in f.readlines()]

# cv2.setNumThreads(6)

classes_list = []
scores_list = []
boxes_list = []
time_begin = time.time()
count = 0
for filename in filenames:
    if count > NUM_IMAGES:
        break
    frame = cv2.imread(filename)
    frame = frame[:, :, ::-1]
    classes, scores, boxes = perception.process_frame(frame)

    classes_list.append(classes)
    scores_list.append(scores)
    boxes_list.append(boxes)

    count += 1
    if count % 100 == 0:
        print('progress: %.1f%%' % (100.0 * (count / len(filenames))))
time_end = time.time()

time_diff = time_end - time_begin
time_per_image = time_diff / len(filenames)
fps = 1.0 / time_per_image

time_file = open('perception/time.txt', 'w')
time_file.write('time begin (s): %f\n' % time_begin)
time_file.write('time end (s): %f\n' % time_end)
time_file.write('time diff (s): %f\n' % time_diff)
time_file.write('time per image (s): %f\n' % time_per_image)
time_file.write('fps: %f\n' % fps)



count = 0
for filename, classes, scores, boxes in zip(filenames, classes_list, scores_list, boxes_list):
    if count > NUM_IMAGES:
        break
    frame = cv2.imread(filename)
    text_log_filename = filename.split('\\')[-1].split('.')[0] + '.txt'
    text_log_file = open(text_logs_dir + '/' + text_log_filename, 'w')
    image_result, result_strings = draw_annotations(frame, classes, scores, boxes)
    for result_str in result_strings:
        text_log_file.write(result_str)
    if count < NUM_IMAGES:
        predictions_filename = filename.split('\\')[-1].split('.')[0] + '.jpg'
        cv2.imwrite(predictions_dir + '/' + predictions_filename, image_result)
    text_log_file.close()
    count += 1
