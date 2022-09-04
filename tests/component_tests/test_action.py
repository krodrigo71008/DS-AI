from action.Action import Action
from control.Control import Control

import pytest


@pytest.fixture
def control_and_action():
    """Generates empty Control and Action instances"""
    return (Control(), Action())

@pytest.mark.parametrize("commands_list, expected_results", [
    ([
        [(["a"], "press"), []],
        [(["b"], "press"), []]
    ],
    [
        [],
        ["a"]
    ]),
    ([
        [(["a"], "press"), []],
        [(["a", "b"], "press"), []],
        [(["c"], "press"), []],
    ],
    [
        [],
        [],
        ["a", "b"]
    ]),
    ([
        [(["a", "b", "c"], "press"), []],
        [(["a", "c"], "press"), []],
        [(["c"], "press"), []],
    ],
    [
        [],
        ["b"],
        ["a"]
    ]),
])

def test_keys_released(control_and_action : tuple[Control, Action], commands_list : list[str], expected_results : list[str]) -> None:
    """Tests Action by sending a few commands with control and seeing which keys would be released

    :param control_and_action: not initialized Control and Action for testing purposes
    :type control_and_action: tuple[Control, Action]
    :param commands_list: list of commands of keys to press
    :type commands_list: list[str]
    :param expected_results: expected released keys after the new command
    :type expected_results: list[str]
    """
    control, action = control_and_action
    for comm, expected_res in zip(commands_list, expected_results):
        control.key_action = comm[0]
        control.mouse_action = comm[1]
        res = action.act_mock(control)
        assert set(res) == set(expected_res)
