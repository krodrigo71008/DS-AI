from action.Action import Action
from control.Control import Control

import pytest


@pytest.fixture
def control_and_action():
    """Generates empty Control and Action instances"""
    return (Control(), Action())

@pytest.mark.parametrize("commands_list, expected_results", [
    ([
        [["a"], []],
        [["b"], []]
    ],
    [
        [],
        ["a"]
    ]),
    ([
        [["a"], []],
        [["a", "b"], []],
        [["c"], []],
    ],
    [
        [],
        [],
        ["a", "b"]
    ]),
    ([
        [["a", "b", "c"], []],
        [["a", "c"], []],
        [["c"], []],
    ],
    [
        [],
        ["b"],
        ["a"]
    ]),
])

def test_action(control_and_action, commands_list, expected_results):
    control, action = control_and_action
    for comm, expected_res in zip(commands_list, expected_results):
        control.key_action = comm[0]
        control.mouse_action = comm[1]
        res = action.act_mock(control)
        assert set(res) == set(expected_res)
