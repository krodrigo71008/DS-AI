import math
import time

from decisionMaking.DecisionMaking import DecisionMaking
from control.Control import Control
from action.Action import Action
from modeling.Modeling import Modeling

def try_out_complex_action():
    modeling = Modeling()
    decision_making = DecisionMaking()
    control = Control(debug=True)
    action = Action()
    # list of some interesting actions to test:
    # ("craft", ["Torch"])
    # ("equip", "Torch"), but you have to add it to your inventory
    # ("eat", "Berries"), but you have to add it to your inventory
    # ("run", 0.0) # expected to run bottom right
    # ("run", -math.pi/4) # expected to run right
    # ("run", math.pi) # expected to run top left
    decision_making.secondary_action = ("equip", "Torch")
    
    # for adding stuff to inventory
    modeling.player_model.inventory.add_item("Torch", 1)
    modeling.player_model.inventory.add_item("Torch", 1)
    # modeling.player_model.inventory.add_item("Berries", 1)

    time.sleep(2)
    start = time.time()
    while time.time() - start < 2:
        control.control(decision_making, modeling)
        action.act(control)
        if control.just_finished_action:
            break
        time.sleep(0.05)
    print("done")