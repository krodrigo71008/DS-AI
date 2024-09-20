from __future__ import annotations
from typing import TYPE_CHECKING
from enum import Enum

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

    def update(self, modeling : Modeling, action_requester : ActionRequester):
        """
        Updates the behavior tree.

        :param modeling: the modeling that will be used to decide the next action
        :param action_requester: records the action to be requested
        """
        if self.root is not None:
            self.root.execute(modeling, action_requester)


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


class LoopNode(TreeNode):
    """
    Represents a loop node of a behavior tree that executes its node while it returns success.
    """
    def __init__(self, node):
        super().__init__(f"Loop {node.node_name}")
        self.looped_node = node

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        pass

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        # Execute the child
        status = self.looped_node.execute(modeling, action_requester)
        while status == ExecutionStatus.SUCCESS:
            status = self.looped_node.execute(modeling, action_requester)
        return status


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


class DSBehaviorTree(BehaviorTree):
    """
    Represents a behavior tree of a Don't Starve AI.
    """
    def __init__(self):
        super().__init__()
        self.root = LoopNode(SelectorNode("Root"))
        self.root.looped_node.add_child(SequenceNode("CheckHandleUnequipTorch"))
        self.root.looped_node.add_child(SequenceNode("CheckHandleGrassTwigs"))
        self.root.looped_node.add_child(SequenceNode("CheckHandleTorch"))
        self.root.looped_node.add_child(GatherFood())
        self.root.looped_node.children[0].add_child(CheckTorchEquipped())
        self.root.looped_node.children[0].add_child(IsDayTime())
        self.root.looped_node.children[0].add_child(UnequipTorch())
        self.root.looped_node.children[1].add_child(NegateNode(CheckEnoughGrassTwigs()))
        self.root.looped_node.children[1].add_child(SelectorNode("GatherGrassTwigs"))
        self.root.looped_node.children[1].children[1].add_child(SequenceNode("CheckHandleKnownResources"))
        self.root.looped_node.children[1].children[1].children[0].add_child(NegateNode(CheckKnownGrassTwigs()))
        self.root.looped_node.children[1].children[1].children[0].add_child(SelectorNode("Explore"))
        self.root.looped_node.children[1].children[1].children[0].children[1].add_child(SequenceNode("CheckHandleNextPoint"))
        self.root.looped_node.children[1].children[1].children[0].children[1].children[0].add_child(CheckNextPointValid())
        self.root.looped_node.children[1].children[1].children[0].children[1].children[0].add_child(GoNextPoint())
        self.root.looped_node.children[1].children[1].children[0].children[1].add_child(GoValidPoint())
        self.root.looped_node.children[1].children[1].add_child(GetKnownResources())
        self.root.looped_node.children[2].add_child(NegateNode(CheckTorch()))
        self.root.looped_node.children[2].add_child(CraftTorch())


class CheckEnoughGrassTwigs(LeafNode):
    def __init__(self):
        super().__init__("CheckEnoughGrassTwigs")

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        pass

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        cut_grass_count = modeling.player_model.inventory.get_inventory_count(["CutGrass"])[0]
        twigs_count = modeling.player_model.inventory.get_inventory_count(["Twigs"])[0]
        if cut_grass_count < 4 or twigs_count < 4:
            return ExecutionStatus.FAILURE
        else:
            return ExecutionStatus.SUCCESS


class CheckKnownGrassTwigs(LeafNode):
    def __init__(self):
        super().__init__("CheckKnownGrassTwigs")

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        pass

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        obj_lists = modeling.world_model.get_all_of(["Grass", "Sapling", "CutGrass", "Twigs"], filter_="only_not_harvested")
        all_objects : list[ObjectModel] = []
        for obj_list in obj_lists.values():
            all_objects = [*all_objects, *obj_list]

        if len(all_objects) == 0:
            return ExecutionStatus.FAILURE
        else:
            return ExecutionStatus.SUCCESS


class CheckNextPointValid(LeafNode):
    def __init__(self):
        super().__init__("CheckNextPointValid")

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        pass

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        if modeling.world_model.check_if_next_target_valid():
            return ExecutionStatus.SUCCESS
        else:
            return ExecutionStatus.FAILURE

class GoNextPoint(LeafNode):
    def __init__(self):
        super().__init__("GoNextPoint")
        self.start_time = None

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        self.start_time = modeling.clock.time()
        # set the behavior
        action_requester.set_action(("go", modeling.world_model.next_exploration_point))

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        if (modeling.world_model.next_exploration_point.distance(modeling.player_position()) 
            >= modeling.world_model.CLOSE_DISTANCE_TO_EXPLORATION_POINT):
            return ExecutionStatus.RUNNING
        elif modeling.clock.time() - self.start_time >= 60:
            return ExecutionStatus.FAILURE
        else:
            return ExecutionStatus.SUCCESS

class GoValidPoint(LeafNode):
    def __init__(self):
        super().__init__("GoValidPoint")
        self.start_time = None

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        modeling.world_model.search_for_valid_exploration_point()
        next_point = modeling.world_model.next_exploration_point

        self.start_time = modeling.clock.time()
        # set the behavior
        action_requester.set_action(("go", next_point))

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        if (modeling.world_model.next_exploration_point.distance(modeling.player_position()) 
            >= modeling.world_model.CLOSE_DISTANCE_TO_EXPLORATION_POINT):
            return ExecutionStatus.RUNNING
        elif modeling.clock.time() - self.start_time >= 60:
            return ExecutionStatus.FAILURE
        else:
            return ExecutionStatus.SUCCESS

class GetKnownResources(LeafNode):
    def __init__(self):
        super().__init__("GetKnownResources")
        self.start_time = None

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        self.start_time = modeling.clock.time()
        # set the behavior
        action_requester.set_action(("gather", ["CutGrass", "Twigs"]))

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        cut_grass_count = modeling.player_model.inventory.get_inventory_count(["CutGrass"])[0]
        twigs_count = modeling.player_model.inventory.get_inventory_count(["Twigs"])[0]
        if cut_grass_count < 4 or twigs_count < 4:
            return ExecutionStatus.RUNNING
        elif modeling.clock.time() - self.start_time >= 60:
            return ExecutionStatus.FAILURE
        else:
            return ExecutionStatus.SUCCESS


class CheckTorch(LeafNode):
    def __init__(self):
        super().__init__("CheckTorch")

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        pass

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        torch_count = modeling.player_model.inventory.get_inventory_count(["Torch"])[0]
        if torch_count < 1:
            return ExecutionStatus.FAILURE
        else:
            return ExecutionStatus.SUCCESS


class CraftTorch(LeafNode):
    def __init__(self):
        super().__init__("CraftTorch")
        self.start_time = None

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        self.start_time = modeling.clock.time()
        # set the behavior
        action_requester.set_action(("craft", ["Torch"]))

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        torch_count = modeling.player_model.inventory.get_inventory_count(["Torch"])[0]
        if torch_count < 1:
            return ExecutionStatus.RUNNING
        elif modeling.clock.time() - self.start_time >= 60:
            return ExecutionStatus.FAILURE
        else:
            return ExecutionStatus.SUCCESS


class CheckTorchEquipped(LeafNode):
    def __init__(self):
        super().__init__("CheckTorchEquipped")

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        pass

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        hand_slot = modeling.player_model.inventory.get_inventory_slots()["Hand"]
        if hand_slot.object is not None and hand_slot.object.name == "Torch":
            return ExecutionStatus.SUCCESS
        else:
            return ExecutionStatus.FAILURE


class IsDayTime(LeafNode):
    def __init__(self):
        super().__init__("IsDayTime")

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        pass

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        if modeling.clock.day_section() != "Night":
            return ExecutionStatus.SUCCESS
        else:
            return ExecutionStatus.FAILURE


class UnequipTorch(LeafNode):
    def __init__(self):
        super().__init__("UnequipTorch")
        self.start_time = None

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        self.start_time = modeling.clock.time()
        # set the behavior
        action_requester.set_action(("unequip", "Hand"))

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        if modeling.player_model.inventory.get_inventory_slots()["Hand"].object is not None:
            return ExecutionStatus.RUNNING
        elif modeling.clock.time() - self.start_time >= 60:
            return ExecutionStatus.FAILURE
        else:
            return ExecutionStatus.SUCCESS


class GatherFood(LeafNode):
    def __init__(self):
        super().__init__("GatherFood")
        self.start_time = None

    def enter(self, modeling : Modeling, action_requester : ActionRequester):
        self.start_time = modeling.clock.time()
        # set the behavior
        action_requester.set_action(("gather", ["food"]))

    def execute(self, modeling : Modeling, action_requester : ActionRequester):
        # This node can't return SUCCESS since it would terminate the behavior tree
        if modeling.clock.time() - self.start_time >= 60:
            return ExecutionStatus.FAILURE
        else:
            return ExecutionStatus.RUNNING
