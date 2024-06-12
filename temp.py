import glob
from pathlib import Path
import pandas as pd

from modeling.Modeling import Modeling
from utility.Point2d import Point2d

GT_PATH = "D:/Programacao/mAP/input/ground-truth"
DIST_THRESHOLD = 20

modeling = Modeling()
models = glob.glob("perception/darknet/models/*.pt")
all_info = pd.DataFrame(columns=["model", "name", "confidence", "error_x1", "error_x2"])
for model in models:
    model_name = Path(model).stem
    result_folder = "perception/test_results/" + model_name
    detection_files = glob.glob(result_folder + "/*.txt")
    gt_files = glob.glob(GT_PATH + "/*.txt")
    assert set([Path(f).name for f in detection_files]) == set([Path(f).name for f in gt_files])
    detection_files = sorted(detection_files, key=lambda x : Path(x).name)
    gt_files = sorted(gt_files, key=lambda x : Path(x).name)
    for detection_file, gt_file in zip(detection_files, gt_files):
        detections_df = pd.DataFrame(columns=["name", "confidence", "x1", "x2"])
        gt_df = pd.DataFrame(columns=["name", "x1", "x2"])
        with open(detection_file, "r") as detection:
            with open(gt_file, "r") as gt:
                detection_lines = detection.readlines()
                gt_lines = gt.readlines()
                temp_list = []
                for detection_line in detection_lines:
                    name, conf, x1, y1, x2, y2 = detection_line.split(" ")
                    conf = float(conf)
                    x1 = float(x1)
                    x2 = float(x2)
                    y1 = float(y1)
                    y2 = float(y2)
                    screen_point = Point2d((x1+x2)/2, y2)
                    temp_list.append({
                        "name": name,
                        "confidence": conf,
                        "x1": screen_point.x1,
                        "x2": screen_point.x2,
                    })
                detections_df = pd.concat([detections_df, pd.DataFrame(temp_list)], ignore_index=True)

                temp_list = []
                for gt_line in gt_lines:
                    name, x1, y1, x2, y2 = gt_line.split(" ")
                    x1 = float(x1)
                    x2 = float(x2)
                    y1 = float(y1)
                    y2 = float(y2)
                    screen_point = Point2d((x1+x2)/2, y2)
                    temp_list.append({
                        "name": name,
                        "x1": screen_point.x1,
                        "x2": screen_point.x2,
                    })
                gt_df = pd.concat([gt_df, pd.DataFrame(temp_list)], ignore_index=True)

                temp_list = []
                for index, row in detections_df.iterrows():
                    name = row["name"]
                    confidence = row["confidence"]
                    detection_x1 = row["x1"]
                    detection_x2 = row["x2"]
                    closest = None
                    closest_dist = None
                    for gt_index, gt_row in gt_df.iterrows():
                        gt_name = gt_row["name"]
                        if gt_name != name:
                            continue
                        gt_x1 = gt_row["x1"]
                        gt_x2 = gt_row["x2"]
                        dist = Point2d(detection_x1, detection_x2).distance(Point2d(gt_x1, gt_x2))
                        if closest is None or closest_dist > dist:
                            closest = Point2d(gt_x1, gt_x2)
                            closest_dist = dist

                    if closest is None or closest_dist > DIST_THRESHOLD:
                        continue
                        
                    error_x1 = closest.x1 - detection_x1
                    error_x2 = closest.x2 - detection_x2
                    temp_list.append({
                        "model": model_name,
                        "name": name,
                        "confidence": confidence,
                        "error_x1": error_x1,
                        "error_x2": error_x2,
                    })
                all_info = pd.concat([all_info, pd.DataFrame(temp_list)], ignore_index=True)

