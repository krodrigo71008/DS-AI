import cv2
import time
import os
import glob
from classes import get_class_names

# images_dir = '../darknet-master/data/obj'
# images_dir = 'augmentation'
images_dir = 'images'
text_logs_dir = 'text_logs'
predictions_dir = 'predictions'
NUM_IMAGES = 863
CONFIDENCE_THRESHOLD = 0.01  # 0.01
NMS_THRESHOLD = 0.45  # 0.4


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


class_names = get_class_names()

filenames = glob.glob(images_dir + '/**/*.jpg', recursive=True)
filenames.extend(glob.glob(images_dir + '/**/*.png', recursive=True))

# images_file = '../darknet-master/data/train.txt'
# with open(images_file) as f:
#     filenames = ['../darknet-master/' + fname.strip() for fname in f.readlines()]

# cv2.setNumThreads(6)

net = cv2.dnn.readNet("darknet/yolov4-custom_best.weights", "darknet/yolov4-custom.cfg")
# net = cv2.dnn.readNet("yolov4-tiny-anchor-obj_last.weights", "yolov4-tiny-anchor-obj.cfg")
# net = cv2.dnn.readNet("yolov4-tiny-obj_best.weights", "yolov4-tiny-obj.cfg")
# net = cv2.dnn.readNet("yolo-obj_last.weights", "yolo-obj.cfg")
# net = cv2.dnn.readNet('frozen_darknet_yolov4_model.xml', 'frozen_darknet_yolov4_model.bin')
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_INFERENCE_ENGINE)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

model = cv2.dnn_DetectionModel(net)
model.setInputParams(size=(416, 416), scale=1 / 255)

classes_list = []
scores_list = []
boxes_list = []
time_begin = time.time()
count = 0
for filename in filenames:
    frame = cv2.imread(filename)
    classes, scores, boxes = model.detect(frame, CONFIDENCE_THRESHOLD, NMS_THRESHOLD)

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

time_file = open('time.txt', 'w')
time_file.write('time begin (s): %f\n' % time_begin)
time_file.write('time end (s): %f\n' % time_end)
time_file.write('time diff (s): %f\n' % time_diff)
time_file.write('time per image (s): %f\n' % time_per_image)
time_file.write('fps: %f\n' % fps)


color = (255, 0, 0)
count = 0
for filename, classes, scores, boxes in zip(filenames, classes_list, scores_list, boxes_list):
    if count < NUM_IMAGES:
        frame = cv2.imread(filename)
    text_log_filename = filename.split('\\')[-1].split('.')[0] + '.txt'
    text_log_file = open(text_logs_dir + '/' + text_log_filename, 'w')
    for class_id, score, box in zip(classes, scores, boxes):
        text_log_file.write('%s %f %f %f %f %f\n' % (class_names[class_id[0]], score, box[0], box[1], box[0] + box[2],
                                                     box[1] + box[3]))
        if count < NUM_IMAGES:
            label = "%s: %f" % (class_names[class_id[0]], score)
            cv2.rectangle(frame, box, color, 2)
            cv2.putText(frame, label, (box[0], box[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    if count < NUM_IMAGES:
        predictions_filename = filename.split('\\')[-1].split('.')[0] + '.jpg'
        cv2.imwrite(predictions_dir + '/' + predictions_filename, frame)
    text_log_file.close()
    count += 1
