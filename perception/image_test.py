import cv2
import mss
import Perception
import numpy as np
from pynput import keyboard
from classes import get_class_names


i = 10


def on_press(key):
    if key == keyboard.Key.esc:
        cv2.destroyAllWindows()
        return False  # stop listener
    try:
        k = key.char  # single-char keys
    except AttributeError:
        k = key.name  # other keys
    if k in ['t']:  # keys of interest
        print("a")
        objects, frame = p.perceive(debug=True)
        # width = 1280
        # height = 720
        # dim = (width, height)

        # resize image
        # resized = cv2.resize(frame, dim, interpolation=cv2.INTER_AREA)
        # cv2.imshow('image', resized)
        frame = np.array(frame)
        global i
        i = i + 1
        with open(f'test_results/image_{i}.txt', 'w') as f:
            for obj in objects:
                label = "%s: %f" % (class_names[obj.id[0]], obj.score)
                cv2.rectangle(frame, obj.box, color, 2)
                cv2.putText(frame, label, (obj.box[0], obj.box[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                f.write(f'{class_names[obj.id[0]]} {obj.score} {obj.box[0]} {obj.box[1]}\n')
        cv2.imshow('image', frame)
        cv2.waitKey(5000)
        cv2.destroyAllWindows()
        cv2.imwrite(f'test_results/image_{i}.png', frame)


p = Perception.Perception()

# 800x600 windowed mode
mon = {"top": 0, "left": 0, "width": 1920, "height": 1080}

sct = mss.mss()

class_names = get_class_names()
color = (255, 0, 0)

listener = keyboard.Listener(on_press=on_press)
listener.start()  # start to listen on a separate thread
listener.join()
