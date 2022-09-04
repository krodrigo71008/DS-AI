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
            if key_action[1] == "press":
                keys_to_release = list(self.current_keys.difference(key_action[0]))
                if len(keys_to_release) > 0:
                    keyboard.release('+'.join(keys_to_release))
                keyboard.press('+'.join(key_action[0]))
                self.current_keys = set(key_action[0])
            elif key_action[1] == "press_and_release":
                if not control.action_on_cooldown:
                    keyboard.press_and_release('+'.join(key_action[0]))
                    self.current_keys = self.current_keys.difference(key_action[0])
        if mouse_action is not None:
            if mouse_action[0] == "click":
                mouse.move(mouse_action[1].x1, mouse_action[1].x2)
                mouse.click()
            elif mouse_action[0] == "right_click":
                mouse.move(mouse_action[1].x1, mouse_action[1].x2)
                mouse.right_click()

    def act_mock(self, control: Control) -> list[str]:
        """Same as act, but doesn't actually perform the action and also returns keys_to_release

        :param control: control layer
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
