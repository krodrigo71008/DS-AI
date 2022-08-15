import glob
import cv2
import numpy as np

from classes import get_class_names

images_dir = "perception/generated_images"
image_filenames = glob.glob(images_dir + '/**/*.png', recursive=True)

predictions_dir = "perception/yolo_test_results"

class_names = get_class_names()

color = (255, 0, 0)
count = 0

for filename in image_filenames:
    frame = cv2.imread(filename)
    width = frame.shape[1]
    height = frame.shape[0]
    text_filename = "".join(filename.split(".")[0:-1])
    text_filename += ".txt"
    with open(text_filename, "r") as annotations:
        lines = annotations.readlines()
        for line in lines:
            info = line.strip().split(" ")
            image_id = info[0]
            label = f"{class_names[int(image_id)]}"
            box = [float(x) for x in info[1:5]]
            box[0] -= box[2]/2
            box[1] -= box[3]/2
            for i, number in enumerate(box):
                if i % 2 == 0:
                    box[i] *= width
                else:
                    box[i] *= height
                box[i] = int(box[i])
            box = np.array(box)
            cv2.rectangle(frame, box, color, 2)
            cv2.putText(frame, label, (box[0], box[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        predictions_filename = filename.split('\\')[-1].split('.')[0] + '.jpg'
        cv2.imwrite(predictions_dir + '/' + predictions_filename, frame)
    count += 1
    if count % 100 == 0:
        print('progress: %.1f%%' % (100.0 * (count / len(image_filenames))))