from typing import List

import keyboard
import mouse

from control.Control import Control


class Action:
    def __init__(self):
        self.current_keys = set()

    def act(self, control: Control):
        # key_action is array of strings
        key_action = control.key_action
        mouse_action = control.mouse_action
        if key_action is not None:
            keys_to_release = list(self.current_keys.difference(key_action))
            if len(keys_to_release) > 0:
                keyboard.release('+'.join(keys_to_release))
            keyboard.press('+'.join(key_action))
            self.current_keys = set(key_action)
        if mouse_action is not None:
            if mouse_action[0] == "click":
                mouse.move(mouse_action[1][0], mouse_action[1][1])
                mouse.click()
            elif mouse_action[0] == "right_click":
                mouse.move(mouse_action[1][0], mouse_action[1][1])
                mouse.right_click()

    def act_mock(self, control: Control):
        # key_action is array of strings
        key_action = control.key_action
        mouse_action = control.mouse_action
        if key_action is not None:
            keys_to_release = list(self.current_keys.difference(key_action))
            self.current_keys = set(key_action)
        return keys_to_release
