import time

import keyboard
import mouse

from control.Control import Control


class Action:
    def __init__(self, debug=False, measure_time=False):
        self.current_keys = set()
        self.debug = debug
        if self.debug:
            self.records = []
        
        self.measure_time = measure_time
        if self.measure_time:
            self.time_records = []

    def act(self, control: Control) -> None:
        """Use mouse and keyboard to perform the action decided by the Control layer

        :param control: Control layer
        :type control: Control
        """
        if self.measure_time:
            t1 = time.time_ns()

        # key_action is array of strings
        key_action = control.key_action
        mouse_action = control.mouse_action
        if key_action is not None:
            if key_action[1] == "press":
                keys_to_release = list(self.current_keys.difference(key_action[0]))
                if len(keys_to_release) > 0:
                    keyboard.release('+'.join(keys_to_release))
                    if self.debug:
                        self.records.append(('release', '+'.join(keys_to_release)))
                keyboard.press('+'.join(key_action[0]))
                if self.debug:
                    self.records.append(('´press', '+'.join(key_action[0])))
                self.current_keys = set(key_action[0])
            elif key_action[1] == "press_and_release":
                # this is probably wrong, but for now just release all keys when doing it
                if not control.action_on_cooldown:
                    if len(self.current_keys) > 0:
                        keyboard.release('+'.join(self.current_keys))
                        self.current_keys = set()
                    keyboard.press_and_release('+'.join(key_action[0]))
                    if self.debug:
                        self.records.append(('press_and_release', '+'.join(key_action[0])))
                    self.current_keys = self.current_keys.difference(key_action[0])
        else:
            if len(self.current_keys) > 0:
                keyboard.release('+'.join(self.current_keys))
        if mouse_action is not None:
            if not control.action_on_cooldown:
                if mouse_action[0] == "click":
                    mouse.move(mouse_action[1].x1, mouse_action[1].x2)
                    mouse.click()
                elif mouse_action[0] == "right_click":
                    mouse.move(mouse_action[1].x1, mouse_action[1].x2)
                    mouse.right_click()
                elif mouse_action[0] == "move":
                    mouse.move(mouse_action[1].x1, mouse_action[1].x2)

        if self.measure_time:
            t2 = time.time_ns()
            self.time_records.append(t2-t1)
        

    def act_mock(self, control: Control) -> list[str]:
        """Same as act, but doesn't actually perform the action and also returns keys_to_release

        :param control: Control layer
        :type control: Control
        :return: list of all keys that would be released if this wasn't a mock
        :rtype: list[str]
        """
        # key_action is array of strings
        key_action = control.key_action
        mouse_action = control.mouse_action
        keys_to_release = list(self.current_keys.difference(key_action[0]))
        if key_action is not None:
            if key_action[1] == "press":
                self.current_keys = set(key_action[0])
            elif key_action[1] == "press_and_release":
                if not control.action_on_cooldown:
                    self.current_keys = self.current_keys.difference(key_action[0])
        return keys_to_release
