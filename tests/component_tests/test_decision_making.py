from decisionMaking.BehaviorTrees import CheckResourcesForScienceAndAlchemy, ExecutionStatus
from modeling.Modeling import Modeling

def test_check_resources_for_science_and_alchemy():
    mod = Modeling()
    bt = CheckResourcesForScienceAndAlchemy()
    assert bt.execute(mod, None) == ExecutionStatus.FAILURE
    mod.player_model.inventory.add_item("Log", 20)
    mod.player_model.inventory.add_item("GoldNugget", 8)
    mod.player_model.inventory.add_item("Rocks", 10)
    assert bt.execute(mod, None) == ExecutionStatus.SUCCESS