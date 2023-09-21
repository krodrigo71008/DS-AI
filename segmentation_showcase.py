import time
from multiprocessing import Process, Queue, Value

import keyboard

from perception.SegmentationModel import SegmentationModel
from utility.SegmentationVisualizer import SegmentationVisualizer


def segmentation_main(should_start: Value, should_stop: Value, q: Queue = None):
    seg_model = SegmentationModel(debug=q is not None, queue=q)
    while should_start.value == 0:
        pass
    start = time.time()
    while should_stop.value == 0 and time.time() - start < 180:
        seg_model.perceive()

if __name__ == "__main__":
    should_start = Value('b', 0)
    should_stop = Value('b', 0)
    vis_screen = SegmentationVisualizer()
    segmentation_process = Process(target=segmentation_main, 
                                    args=(should_start, should_stop, vis_screen.segmentation_debug_queue))
    segmentation_process.start()
    start = time.time()
    while time.time() - start < 180:
        if keyboard.is_pressed("p"):
            should_start.value = 1
        elif keyboard.is_pressed("l"):
            should_stop.value = 1
        vis_screen.update()
