import math

from modeling.Modeling import Modeling
from modeling.constants import CAMERA_HEADING
from decisionMaking.ActionRequester import ActionRequester
from decisionMaking.BehaviorTrees import RotateCameraBehaviorTree, ExecutionStatus
from control.constants import CAMERA_ROTATION_DURATION

def test_rotate_behavior_tree():
    modeling = Modeling()
    action_requester = ActionRequester()
    objective_angle = math.pi/2
    bt = RotateCameraBehaviorTree(objective_angle)

    assert modeling.world_model.heading == CAMERA_HEADING
    
    assert modeling.do_image_processing == True
    assert bt.update(modeling, action_requester) == ExecutionStatus.RUNNING
    assert modeling.do_image_processing == False
    assert bt.get_running_leaf() == "RotateCamera"
    assert action_requester.get_action() == ("press_and_release", ["q"])
    assert action_requester.get_resources_request() is None

    modeling.clock.time_in_seconds += CAMERA_ROTATION_DURATION/2 # not finished yet
    action_requester.set_action(None)
    
    assert bt.update(modeling, action_requester) == ExecutionStatus.RUNNING
    assert modeling.do_image_processing == False
    assert bt.get_running_leaf() == "RotateCamera"
    assert modeling.world_model.heading == CAMERA_HEADING
    assert action_requester.get_action() is None
    assert action_requester.get_resources_request() is None

    modeling.clock.time_in_seconds += CAMERA_ROTATION_DURATION # finished rotation
    action_requester.set_action(None)
    
    assert bt.update(modeling, action_requester) == ExecutionStatus.RUNNING
    assert modeling.do_image_processing == False
    assert bt.get_running_leaf() == "RotateCamera"
    assert modeling.world_model.heading == CAMERA_HEADING - 45
    assert action_requester.get_action() == ("press_and_release", ["q"])
    assert action_requester.get_resources_request() is None

    modeling.clock.time_in_seconds += CAMERA_ROTATION_DURATION/2 # not finished yet
    action_requester.set_action(None)
    
    assert bt.update(modeling, action_requester) == ExecutionStatus.RUNNING
    assert modeling.do_image_processing == False
    assert bt.get_running_leaf() == "RotateCamera"
    assert modeling.world_model.heading == CAMERA_HEADING - 45
    assert action_requester.get_action() is None
    assert action_requester.get_resources_request() is None

    modeling.clock.time_in_seconds += CAMERA_ROTATION_DURATION # finished rotation
    action_requester.set_action(None)
    
    assert bt.update(modeling, action_requester) == ExecutionStatus.SUCCESS
    assert modeling.do_image_processing == True
    assert bt.get_running_leaf() is None
    assert modeling.world_model.heading == CAMERA_HEADING + 270 # CAMERA_HEADING - 90 + 360
    assert action_requester.get_action() is None
    assert action_requester.get_resources_request() is None

def test_rotate_behavior_tree_2():
    modeling = Modeling()
    action_requester = ActionRequester()
    objective_angle = 0.0
    bt = RotateCameraBehaviorTree(objective_angle)

    assert modeling.world_model.heading == CAMERA_HEADING
    
    assert modeling.do_image_processing == True
    assert bt.update(modeling, action_requester) == ExecutionStatus.RUNNING
    assert modeling.do_image_processing == False
    assert bt.get_running_leaf() == "RotateCamera"
    assert action_requester.get_action() == ("press_and_release", ["e"])
    assert action_requester.get_resources_request() is None

    modeling.clock.time_in_seconds += CAMERA_ROTATION_DURATION/2 # not finished yet
    action_requester.set_action(None)
    
    assert bt.update(modeling, action_requester) == ExecutionStatus.RUNNING
    assert modeling.do_image_processing == False
    assert bt.get_running_leaf() == "RotateCamera"
    assert modeling.world_model.heading == CAMERA_HEADING
    assert action_requester.get_action() is None
    assert action_requester.get_resources_request() is None

    modeling.clock.time_in_seconds += CAMERA_ROTATION_DURATION # finished rotation
    action_requester.set_action(None)
    
    assert bt.update(modeling, action_requester) == ExecutionStatus.RUNNING
    assert modeling.do_image_processing == False
    assert bt.get_running_leaf() == "RotateCamera"
    assert modeling.world_model.heading == CAMERA_HEADING + 45
    assert action_requester.get_action() == ("press_and_release", ["e"])
    assert action_requester.get_resources_request() is None

    modeling.clock.time_in_seconds += CAMERA_ROTATION_DURATION/2 # not finished yet
    action_requester.set_action(None)
    
    assert bt.update(modeling, action_requester) == ExecutionStatus.RUNNING
    assert modeling.do_image_processing == False
    assert bt.get_running_leaf() == "RotateCamera"
    assert modeling.world_model.heading == CAMERA_HEADING + 45
    assert action_requester.get_action() is None
    assert action_requester.get_resources_request() is None

    modeling.clock.time_in_seconds += CAMERA_ROTATION_DURATION # finished rotation
    action_requester.set_action(None)
    
    assert bt.update(modeling, action_requester) == ExecutionStatus.SUCCESS
    assert modeling.do_image_processing == True
    assert bt.get_running_leaf() is None
    assert modeling.world_model.heading == CAMERA_HEADING + 90
    assert action_requester.get_action() is None
    assert action_requester.get_resources_request() is None
