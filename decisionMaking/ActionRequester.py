from typing import Tuple, List


class ActionRequester(object):
    def __init__(self):
        self.action = None

    def set_action(self, action: Tuple[str, List[str]]) -> None:
        self.action = action

    def get_action(self) -> Tuple[str, List[str]]:
        return self.action
