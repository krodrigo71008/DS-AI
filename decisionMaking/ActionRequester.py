class ActionRequester(object):
    def __init__(self):
        self.action = None
        self.resources_request = None

    def set_action(self, action: tuple[str, str]) -> None:
        self.action = action

    def get_action(self) -> tuple[str, str]:
        return self.action

    def set_resources_request(self, resources_request: list[tuple[str, int]]) -> None:
        self.resources_request = resources_request

    def get_resources_request(self) -> list[tuple[str, int]]:
        return self.resources_request
    

