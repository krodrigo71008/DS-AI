from __future__ import annotations
from typing import TYPE_CHECKING
from enum import Enum
import math

import numpy as np

from modeling.objects.PickableObjectModel import PickableObjectModel
from modeling.ObjectsInfo import objects_info
from control.constants import CRAFT_KEYPRESS_DURATION, CLOSE_ENOUGH_DISTANCE, CLOSE_ENOUGH_DISTANCE_FOR_EXPLORATION
from control.constants import COLLECT_DURATION, CAMERA_ROTATION_DURATION
from utility.utility import clamp2pi

if TYPE_CHECKING:
    from modeling.Modeling import Modeling
    from modeling.objects.ObjectModel import ObjectModel
    from decisionMaking.ActionRequester import ActionRequester


class ExecutionStatus(Enum):
    """
    Represents the execution status of a behavior tree node.
    """
    SUCCESS = 0
    FAILURE = 1
    RUNNING = 2


class BehaviorTree(object):
    """
    Represents a behavior tree.
    """
    def __init__(self, root : TreeNode=None):
        """
        Creates a behavior tree.

        :param root: the behavior tree's root node.
        :type root: TreeNode
        """
        self.root = root

    def update(self, modeling : Modeling, action_requester : ActionRequester) -> ExecutionStatus:
        """
        Updates the behavior tree.

        :param modeling: the modeling that will be used to decide the next action
        :param action_requester: records the action to be requested
        :return: status of the root node
        """
        if self.root is not None:
            return self.root.execute(modeling, action_requester)

    def get_running_leaf(self):
        return self.root.get_running_leaf()
                

class TreeNode(object):
    """
    Represents a node of a behavior tree.
    """
    def __init__(self, node_name : str):
        """
        Creates a node of a behavior tree.

        :param node_name: the name of the node.
        :type node_name: string
        """
        self.node_name = node_name
        self.parent = None

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        """
        This method is executed when this node is entered.

        """
        raise NotImplementedError("This method is abstract and must be implemented in derived classes")

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        """
        Executes the behavior tree node logic.

        :return: node status (success, failure or running)
        :rtype: ExecutionStatus
        """
        raise NotImplementedError("This method is abstract and must be implemented in derived classes")

    def get_running_leaf(self):
        """
        Gets leaf that's being executed.

        :return: node name
        :rtype: str
        """
        raise NotImplementedError("This method is abstract and must be implemented in derived classes")


class NegateNode(TreeNode):
    """
    Represents a negate node of a behavior tree.
    """
    def __init__(self, node: TreeNode):
        super().__init__(f"Not {node.node_name}")
        self.negated_node = node

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        pass

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        # Execute the child
        status = self.negated_node.execute(modeling, action_requester)
        if status == ExecutionStatus.FAILURE:
            # Negate the child's return value
            return ExecutionStatus.SUCCESS
        elif status == ExecutionStatus.RUNNING:
            # If the child is still running, then this node is also running
            return ExecutionStatus.RUNNING
        elif status == ExecutionStatus.SUCCESS:
            # Negate the child's return value
            return ExecutionStatus.FAILURE

    def get_running_leaf(self):
        return self.negated_node.get_running_leaf()


class LoopNode(TreeNode):
    """
    Represents a loop node of a behavior tree that executes its node while it returns success.
    """
    def __init__(self, node):
        super().__init__(f"Loop {node.node_name}")
        self.looped_node : TreeNode = node

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        pass

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        # Execute the child
        status = self.looped_node.execute(modeling, action_requester)
        while status == ExecutionStatus.SUCCESS:
            status = self.looped_node.execute(modeling, action_requester)
        return status

    def get_running_leaf(self):
        return self.looped_node.get_running_leaf()


class LeafNode(TreeNode):
    """
    Represents a leaf node of a behavior tree.
    """
    def __init__(self, node_name):
        super().__init__(node_name)

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        """
        This method is executed when this node is entered.

        """
        raise NotImplementedError("This method is abstract and must be implemented in derived classes")

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        """
        Executes the behavior tree node logic.

        :return: node status (success, failure or running)
        :rtype: ExecutionStatus
        """
        raise NotImplementedError("This method is abstract and must be implemented in derived classes")

    def get_running_leaf(self):
        return self.__class__.__name__


class CompositeNode(TreeNode):
    """
    Represents a composite node of a behavior tree.
    """
    def __init__(self, node_name):
        super().__init__(node_name)
        self.children : list[TreeNode] = []

    def add_child(self, child):
        """
        Adds a child to this composite node.

        :param child: child to be added to this node.
        :type child: TreeNode
        """
        child.parent = self
        self.children.append(child)

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        """
        This method is executed when this node is entered.

        """
        raise NotImplementedError("This method is abstract and must be implemented in derived classes")

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        """
        Executes the behavior tree node logic.

        :return: node status (success, failure or running)
        :rtype: ExecutionStatus
        """
        raise NotImplementedError("This method is abstract and must be implemented in derived classes")

    def get_running_leaf(self):
        raise NotImplementedError("This method is abstract and must be implemented in derived classes")


class SequenceNode(CompositeNode):
    """
    Represents a sequence node of a behavior tree.
    """
    def __init__(self, node_name):
        super().__init__(node_name)
        # We need to keep track of the last running child when resuming the tree execution
        self.running_child = None

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        # When this node is entered, no child should be running
        self.running_child = None

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        if self.running_child is None:
            # If a child was not running, then the node puts its first child to run
            self.running_child = self.children[0]
            self.running_child.enter(modeling, action_requester)
        loop = True
        while loop:
            # Execute the running child
            status = self.running_child.execute(modeling, action_requester)
            if status == ExecutionStatus.FAILURE:
                # This is a sequence node, so any failure results in the node failing
                self.running_child = None
                return ExecutionStatus.FAILURE
            elif status == ExecutionStatus.RUNNING:
                # If the child is still running, then this node is also running
                return ExecutionStatus.RUNNING
            elif status == ExecutionStatus.SUCCESS:
                # If the child returned success, then we need to run the next child or declare success
                # if this was the last child
                index = self.children.index(self.running_child)
                if index + 1 < len(self.children):
                    self.running_child = self.children[index + 1]
                    self.running_child.enter(modeling, action_requester)
                else:
                    self.running_child = None
                    return ExecutionStatus.SUCCESS

    def get_running_leaf(self):
        if self.running_child is None:
            return None
        return self.running_child.get_running_leaf()


class SelectorNode(CompositeNode):
    """
    Represents a selector node of a behavior tree.
    """
    def __init__(self, node_name):
        super().__init__(node_name)
        # We need to keep track of the last running child when resuming the tree execution
        self.running_child = None

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        # When this node is entered, no child should be running
        self.running_child = None

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        if self.running_child is None:
            # If a child was not running, then the node puts its first child to run
            self.running_child = self.children[0]
            self.running_child.enter(modeling, action_requester)
        loop = True
        while loop:
            # Execute the running child
            status = self.running_child.execute(modeling, action_requester)
            if status == ExecutionStatus.FAILURE:
                # This is a selector node, so if the current node failed, we have to try the next one.
                # If there is no child left, then all children failed and the node must declare failure.
                index = self.children.index(self.running_child)
                if index + 1 < len(self.children):
                    self.running_child = self.children[index + 1]
                    self.running_child.enter(modeling, action_requester)
                else:
                    self.running_child = None
                    return ExecutionStatus.FAILURE
            elif status == ExecutionStatus.RUNNING:
                # If the child is still running, then this node is also running
                return ExecutionStatus.RUNNING
            elif status == ExecutionStatus.SUCCESS:
                # If any child returns success, then this node must also declare success
                self.running_child = None
                return ExecutionStatus.SUCCESS

    def get_running_leaf(self):
        return self.running_child.get_running_leaf()


class DSBehaviorTree(BehaviorTree):
    """
    Represents a behavior tree of a Don't Starve AI.
    """
    def __init__(self):
        super().__init__()
        self.root = SequenceNode("Root")
        self.root.add_child(WaitForSegmentationInfo())
        self.root.add_child(SequenceNode("MainNode"))
        self.root.children[1].add_child(NegateNode(LoopNode(SequenceNode("CheckExploreBorders"))))
        self.root.children[1].children[0].negated_node.looped_node.add_child(NegateNode(SelectorNode("CheckShouldExplore")))
        self.root.children[1].children[0].negated_node.looped_node.children[0].negated_node.add_child(IsDay4())
        self.root.children[1].children[0].negated_node.looped_node.children[0].negated_node.add_child(EnoughResourcesForScienceAndAlchemy())
        self.root.children[1].children[0].negated_node.looped_node.add_child(ExploreAroundOcean())
        self.root.children[1].add_child(SequenceNode("BaseConstruction"))
        self.root.children[1].children[1].add_child(MakeScienceMachine())
        self.root.children[1].children[1].add_child(MakeBackpack())
        self.root.children[1].add_child(DoNothing())


class WaitForSegmentationInfo(LeafNode):
    def __init__(self):
        super().__init__("WaitForSegmentationInfo")

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        action_requester.set_action(("nothing", None))

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        if modeling.world_model.tile_manager.detection_count < modeling.world_model.tile_manager._MAX_QUEUE_SIZE:
            return ExecutionStatus.RUNNING
        else:
            return ExecutionStatus.SUCCESS

class DoNothing(LeafNode):
    def __init__(self):
        super().__init__("DoNothing")

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        action_requester.set_action(("nothing", None))

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        return ExecutionStatus.RUNNING

class MakeScienceMachine(LeafNode):
    def __init__(self):
        super().__init__("MakeScienceMachine")
        self.start_time = None

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        action_requester.set_action(("craft", "ScienceMachine"))
        self.start_time = modeling.clock.time()

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        if modeling.clock.time() - self.start_time >= 60:
            return ExecutionStatus.FAILURE
        elif len(modeling.world_model.get_all_of(["ScienceMachine"])["ScienceMachine"]) == 0:
            return ExecutionStatus.RUNNING
        else:
            return ExecutionStatus.SUCCESS

class MakeBackpack(LeafNode):
    def __init__(self):
        super().__init__("MakeBackpack")
        self.start_time = None

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        action_requester.set_action(("craft", "Backpack"))
        self.start_time = modeling.clock.time()

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        if modeling.clock.time() - self.start_time >= 60:
            return ExecutionStatus.FAILURE
        elif (modeling.player_model.inventory.slots["body"].object is None
              or modeling.player_model.inventory.slots["body"].object.name != "Backpack"):
            return ExecutionStatus.RUNNING
        else:
            return ExecutionStatus.SUCCESS

class IsDay4(LeafNode):
    def __init__(self):
        super().__init__("IsDay4")

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        pass

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        if modeling.clock.day() < 4:
            return ExecutionStatus.FAILURE
        else:
            return ExecutionStatus.SUCCESS

class EnoughResourcesForScienceAndAlchemy(LeafNode):
    def __init__(self):
        super().__init__("EnoughResourcesForScienceAndAlchemy")

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        pass

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        materials = objects_info.calculate_raw_resources([("ScienceMachine", 1), ("AlchemyEngine", 1)], "name")
        if modeling.player_model.inventory.check_sufficient_resources(materials):
            return ExecutionStatus.SUCCESS
        else:
            return ExecutionStatus.FAILURE

class ExploreAroundOcean(LeafNode):
    def __init__(self):
        super().__init__("ExploreAroundOcean")
        self.start_time = None

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        self.start_time = modeling.clock.time()
        # set the behavior
        action_requester.set_action(("explore", "ocean"))
        action_requester.set_resources_request([
            ("Twigs", 20),
            ("CutGrass", 20),
            ("Flint", 20),
            ("GoldNugget", 10),
            ("Rocks", 40),
            ("Berries", 20),
            ])

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        if modeling.clock.time() - self.start_time >= 60:
            return ExecutionStatus.FAILURE
        else:
            return ExecutionStatus.RUNNING
        
class OceanExplorationBehaviorTree(BehaviorTree):
    """
    Represents a behavior tree of the Ocean Exploration Behavior.
    """
    def __init__(self):
        super().__init__()
        self.root = LoopNode(SelectorNode("MainLoop"))
        self.root.looped_node.add_child(SequenceNode("CheckHasSeenOcean"))
        self.root.looped_node.add_child(GoSomewhere())
        self.root.looped_node.children[0].add_child(HasSeenOcean())
        self.root.looped_node.children[0].add_child(SelectorNode("ExploreAroundOcean"))
        self.root.looped_node.children[0].children[1].add_child(SequenceNode("CheckVisibleOcean"))
        self.root.looped_node.children[0].children[1].add_child(GoBackToPreviousOceanPoint())
        self.root.looped_node.children[0].children[1].children[0].add_child(CloseToOcean())
        self.root.looped_node.children[0].children[1].children[0].add_child(GoToNextOceanPoint())

class GoSomewhere(LeafNode):
    def __init__(self):
        super().__init__("GoSomewhere")
        self.start_time = None

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        modeling.world_model.make_next_exploration_point()
        self.start_time = modeling.clock.time()

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        if modeling.clock.time() - self.start_time >= 60:
            return ExecutionStatus.FAILURE
        elif (modeling.world_model.next_exploration_point.distance(modeling.player_position()) 
            >= CLOSE_ENOUGH_DISTANCE_FOR_EXPLORATION):
            action_requester.set_action(("request_go", modeling.world_model.next_exploration_point))
            return ExecutionStatus.RUNNING
        else:
            return ExecutionStatus.SUCCESS

class HasSeenOcean(LeafNode):
    def __init__(self):
        super().__init__("HasSeenOcean")

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        pass

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        if modeling.world_model.has_seen_ocean():
            return ExecutionStatus.SUCCESS
        else:
            return ExecutionStatus.FAILURE

class GoBackToPreviousOceanPoint(LeafNode):
    def __init__(self):
        super().__init__("GoBackToPreviousOceanPoint")
        self.start_time = None

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        self.start_time = modeling.clock.time()

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        if modeling.clock.time() - self.start_time >= 60:
            return ExecutionStatus.FAILURE
        elif (modeling.world_model.next_exploration_point.distance(modeling.player_position()) 
            >= CLOSE_ENOUGH_DISTANCE_FOR_EXPLORATION):
            action_requester.set_action(("request_go", modeling.world_model.next_exploration_point))
            return ExecutionStatus.RUNNING
        else:
            return ExecutionStatus.SUCCESS

class CloseToOcean(LeafNode):
    def __init__(self):
        super().__init__("CloseToOcean")

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        pass

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        # next_exploration_point being None means that we need to create the new point,
        # so we need to run GoToNextOceanPoint
        if (modeling.world_model.next_exploration_point is None or
            modeling.world_model.next_exploration_point.distance(modeling.player_position()) < CLOSE_ENOUGH_DISTANCE_FOR_EXPLORATION):
            return ExecutionStatus.SUCCESS
        else:
            return ExecutionStatus.FAILURE

class GoToNextOceanPoint(LeafNode):
    def __init__(self):
        super().__init__("GoToNextOceanPoint")
        self.start_time = None

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        modeling.world_model.search_for_valid_exploration_point()
        self.start_time = modeling.clock.time()

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        if modeling.clock.time() - self.start_time >= 60:
            return ExecutionStatus.FAILURE
        elif (modeling.world_model.next_exploration_point.distance(modeling.player_position()) 
            >= CLOSE_ENOUGH_DISTANCE_FOR_EXPLORATION):
            action_requester.set_action(("request_go", modeling.world_model.next_exploration_point))
            return ExecutionStatus.RUNNING
        else:
            return ExecutionStatus.SUCCESS

class CraftBehaviorTree(BehaviorTree):
    """
    Represents a behavior tree of the Craft Behavior.
    """
    def __init__(self):
        super().__init__()
        self.root = SequenceNode("MainNode")
        self.root.add_child(SelectorNode("CheckCraftingOpen"))
        self.root.children[0].add_child(IsCraftingOpen())
        self.root.children[0].add_child(OpenCraftingMenu())
        self.root.add_child(NegateNode(LoopNode(SequenceNode("CheckCraftingTab"))))
        self.root.children[1].negated_node.looped_node.add_child(IsCraftingTabWrong())
        self.root.children[1].negated_node.looped_node.add_child(SelectorNode("HandleWrongCraftingTab"))
        self.root.children[1].negated_node.looped_node.children[1].add_child(SequenceNode("CheckIfCorrectTabIsUp"))
        self.root.children[1].negated_node.looped_node.children[1].children[0].add_child(IsCorrectTabUp())
        self.root.children[1].negated_node.looped_node.children[1].children[0].add_child(NavigateUp())
        self.root.children[1].negated_node.looped_node.children[1].add_child(NavigateDown())
        self.root.add_child(NegateNode(LoopNode(SequenceNode("CheckCraftingPosition"))))
        self.root.children[1].negated_node.looped_node.add_child(IsCraftingPositionWrong())
        self.root.children[1].negated_node.looped_node.add_child(SelectorNode("HandleWrongCraftingPosition"))
        self.root.children[1].negated_node.looped_node.children[1].add_child(SequenceNode("CheckIfCorrectPositionIsLeft"))
        self.root.children[1].negated_node.looped_node.children[1].children[0].add_child(IsCorrectPositionLeft())
        self.root.children[1].negated_node.looped_node.children[1].children[0].add_child(NavigateLeft())
        self.root.children[1].negated_node.looped_node.children[1].add_child(NavigateRight())
        self.root.add_child(ConfirmCraft())

class IsCraftingOpen(LeafNode):
    def __init__(self):
        super().__init__("IsCraftingOpen")

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        pass

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        if modeling.crafting_model.crafting_open:
            return ExecutionStatus.SUCCESS
        else:
            return ExecutionStatus.FAILURE

class OpenCraftingMenu(LeafNode):
    def __init__(self):
        super().__init__("OpenCraftingMenu")
        self.start_time = None

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        self.start_time = modeling.clock.time()
        # set the behavior
        action_requester.set_action(("press_and_release", ["caps_lock"]))

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        if modeling.clock.time() - self.start_time >= CRAFT_KEYPRESS_DURATION:
            modeling.crafting_model.crafting_open = True
            return ExecutionStatus.SUCCESS
        else:
            return ExecutionStatus.RUNNING

class IsCraftingTabWrong(LeafNode):
    def __init__(self):
        super().__init__("IsCraftingTabWrong")

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        pass

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        wanted_position = modeling.crafting_model.name_to_craft_position[modeling.crafting_model.next_craft]
        if wanted_position[0] == modeling.crafting_model.current_crafting_tab:
            return ExecutionStatus.FAILURE
        else:
            return ExecutionStatus.SUCCESS

class IsCraftingPositionWrong(LeafNode):
    def __init__(self):
        super().__init__("IsCraftingPositionWrong")

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        pass

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        wanted_position = modeling.crafting_model.name_to_craft_position[modeling.crafting_model.next_craft]
        if wanted_position[1] == modeling.crafting_model.crafting_tabs_states[modeling.crafting_model.current_crafting_tab]:
            return ExecutionStatus.FAILURE
        else:
            return ExecutionStatus.SUCCESS

class ConfirmCraft(LeafNode):
    def __init__(self):
        super().__init__("ConfirmCraft")
        self.start_time = None

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        self.start_time = modeling.clock.time()
        # set the behavior
        action_requester.set_action(("press_and_release", ["enter"]))

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        if modeling.clock.time() - self.start_time >= CRAFT_KEYPRESS_DURATION:
            modeling.crafting_model.crafting_open = False
            modeling.crafting_model.next_craft = None
            return ExecutionStatus.SUCCESS
        else:
            return ExecutionStatus.RUNNING

class NavigateRight(LeafNode):
    def __init__(self):
        super().__init__("NavigateRight")
        self.start_time = None

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        self.start_time = modeling.clock.time()
        # set the behavior
        action_requester.set_action(("press_and_release", ["d"]))

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        if modeling.clock.time() - self.start_time >= CRAFT_KEYPRESS_DURATION:
            modeling.crafting_model.crafting_tabs_states[modeling.crafting_model.current_crafting_tab] += 1
            return ExecutionStatus.SUCCESS
        else:
            return ExecutionStatus.RUNNING

class IsCorrectPositionLeft(LeafNode):
    def __init__(self):
        super().__init__("IsCorrectPositionLeft")

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        pass

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        wanted_position = modeling.crafting_model.name_to_craft_position[modeling.crafting_model.next_craft]
        if wanted_position[1] < modeling.crafting_model.crafting_tabs_states[modeling.crafting_model.current_crafting_tab]:
            return ExecutionStatus.SUCCESS
        else:
            return ExecutionStatus.FAILURE

class NavigateLeft(LeafNode):
    def __init__(self):
        super().__init__("NavigateLeft")
        self.start_time = None

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        self.start_time = modeling.clock.time()
        # set the behavior
        action_requester.set_action(("press_and_release", ["a"]))

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        if modeling.clock.time() - self.start_time >= CRAFT_KEYPRESS_DURATION:
            modeling.crafting_model.crafting_tabs_states[modeling.crafting_model.current_crafting_tab] -= 1
            return ExecutionStatus.SUCCESS
        else:
            return ExecutionStatus.RUNNING

class NavigateDown(LeafNode):
    def __init__(self):
        super().__init__("NavigateDown")
        self.start_time = None

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        self.start_time = modeling.clock.time()
        # set the behavior
        action_requester.set_action(("press_and_release", ["s"]))

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        if modeling.clock.time() - self.start_time >= CRAFT_KEYPRESS_DURATION:
            modeling.crafting_model.current_crafting_tab += 1
            return ExecutionStatus.SUCCESS
        else:
            return ExecutionStatus.RUNNING

class IsCorrectTabUp(LeafNode):
    def __init__(self):
        super().__init__("IsCorrectTabUp")

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        pass

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        wanted_position = modeling.crafting_model.name_to_craft_position[modeling.crafting_model.next_craft]
        if wanted_position[0] < modeling.crafting_model.current_crafting_tab:
            return ExecutionStatus.SUCCESS
        else:
            return ExecutionStatus.FAILURE

class NavigateUp(LeafNode):
    def __init__(self):
        super().__init__("NavigateUp")
        self.start_time = None

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        self.start_time = modeling.clock.time()
        # set the behavior
        action_requester.set_action(("press_and_release", ["w"]))

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        if modeling.clock.time() - self.start_time >= CRAFT_KEYPRESS_DURATION:
            modeling.crafting_model.current_crafting_tab -= 1
            return ExecutionStatus.SUCCESS
        else:
            return ExecutionStatus.RUNNING

class CollectSomethingBehaviorTree(BehaviorTree):
    """
    Represents a behavior tree of the Craft Behavior.
    """
    def __init__(self, objective : ObjectModel):
        super().__init__()
        self.objective = objective
        self.root = SequenceNode("MainNode")
        self.root.add_child(SelectorNode("CheckDistance"))
        self.root.add_child(CollectSomething(objective))
        self.root.children[0].add_child(CloseEnough(objective))
        self.root.children[0].add_child(MoveCloser(objective))

class CloseEnough(LeafNode):
    def __init__(self, objective : ObjectModel):
        super().__init__("CloseEnough")
        self.start_time = None
        self.objective = objective

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        pass

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        if modeling.player_position().distance(self.objective) >= CLOSE_ENOUGH_DISTANCE:
            return ExecutionStatus.RUNNING
        else:
            return ExecutionStatus.SUCCESS

class MoveCloser(LeafNode):
    def __init__(self, objective : ObjectModel):
        super().__init__("MoveCloser")
        self.start_time = None
        self.objective = objective

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        self.start_time = modeling.clock.time()

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        if modeling.clock.time() - self.start_time >= 60:
            return ExecutionStatus.FAILURE
        elif modeling.player_position().distance(self.objective.position()) >= CLOSE_ENOUGH_DISTANCE:
            action_requester.set_action(("request_go", self.objective))
            return ExecutionStatus.RUNNING
        else:
            return ExecutionStatus.SUCCESS

class CollectSomething(LeafNode):
    def __init__(self, objective : ObjectModel):
        super().__init__("CollectSomething")
        self.start_time = None
        self.objective = objective

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        self.start_time = modeling.clock.time()
        action_requester.set_action(("press_and_release", ["space"]))

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        if modeling.clock.time() - self.start_time < COLLECT_DURATION:
            return ExecutionStatus.RUNNING
        else:
            return ExecutionStatus.SUCCESS

class RotateCameraBehaviorTree(BehaviorTree):
    """
    Represents a behavior tree of the Craft Behavior.
    """
    def __init__(self, objective_angle : float):
        super().__init__()
        self.root = SequenceNode("MainNode")
        self.root.add_child(WaitTwoSeconds())
        self.root.add_child(StartRotation())
        self.root.add_child(NegateNode(LoopNode(SequenceNode("CheckAngle"))))
        self.root.add_child(FinishRotation())
        self.root.children[2].negated_node.looped_node.add_child(IsCameraAngleWrong(objective_angle))
        self.root.children[2].negated_node.looped_node.add_child(RotateCamera(objective_angle))
        self.root.children[2].negated_node.looped_node.add_child(ConfirmRotation())

class WaitTwoSeconds(LeafNode):
    def __init__(self):
        super().__init__("WaitTwoSeconds")
        self.start_time = None

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        self.start_time = modeling.clock.time()
        action_requester.set_action(("nothing", None))

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        if modeling.clock.time() - self.start_time >= 2:
            return ExecutionStatus.SUCCESS
        else:
            return ExecutionStatus.RUNNING

class StartRotation(LeafNode):
    def __init__(self):
        super().__init__("StartRotation")

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        modeling.do_image_processing = False

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        print("StartRotation")
        return ExecutionStatus.SUCCESS

class FinishRotation(LeafNode):
    def __init__(self):
        super().__init__("FinishRotation")

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        modeling.do_image_processing = True

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        print("FinishRotation")
        return ExecutionStatus.SUCCESS

class IsCameraAngleWrong(LeafNode):
    def __init__(self, objective_angle : float):
        super().__init__("IsCameraAngleWrong")
        self.objective_angle = objective_angle

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        pass

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        angle_difference = clamp2pi(modeling.world_model.heading/180*math.pi - self.objective_angle)
        if angle_difference <= math.pi/2 and angle_difference >= -math.pi/2:
            return ExecutionStatus.SUCCESS
        else:
            return ExecutionStatus.FAILURE

class RotateCamera(LeafNode):
    def __init__(self, objective_angle : float):
        super().__init__("RotateCamera")
        self.objective_angle = objective_angle
        self.start_time = None
        self.action = None

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        self.start_time = modeling.clock.time()
        angle_difference = clamp2pi(modeling.world_model.heading/180*math.pi - self.objective_angle)
        if angle_difference > 0:
            self.action = "e"
        else:
            self.action = "q"
        action_requester.set_action(("press_and_release", [self.action]))
        modeling.set_record_image_diffs(True)

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        if modeling.clock.time() - self.start_time >= CAMERA_ROTATION_DURATION:
            return ExecutionStatus.SUCCESS
        else:
            return ExecutionStatus.RUNNING

class ConfirmRotation(LeafNode):
    def __init__(self):
        super().__init__("ConfirmRotation")
        self.action = None

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        self.action = self.parent.children[1].action

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        modeling.set_record_image_diffs(False)
        diffs = modeling.last_image_diffs
        above_rate = np.sum(diffs > np.mean(diffs))/len(diffs)
        if above_rate <= 0.3 and np.std(diffs) > 1.5:
            if self.action == "e":
                modeling.world_model.turn_camera_right_e()
            else:
                modeling.world_model.turn_camera_left_q()
        return ExecutionStatus.SUCCESS
