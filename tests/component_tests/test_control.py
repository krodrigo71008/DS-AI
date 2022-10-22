import math
import time

from decisionMaking.DecisionMaking import DecisionMaking
from control.Control import Control
from action.Action import Action
from modeling.Modeling import Modeling
from modeling.objects.Grass import Grass, GRASS_READY
from utility.Point2d import Point2d

def try_out_complex_action():
    modeling = Modeling()
    decision_making = DecisionMaking()
    control = Control(debug=True)
    action = Action()
    # list of some interesting actions to test:
    # ("craft", ["Torch"])
    # ("equip", "Torch"), but you have to add it to your inventory
    # ("eat", "Berries"), but you have to add it to your inventory
    # ("run", 0.0) # expected to run bottom left
    # ("run", -math.pi/4) # expected to run left
    # ("run", math.pi/2) # expected to run bottom right
    # ("go_to", Point2d(6, 6)) # expected to go down
    # grass = Grass(Point2d(4, 0), (500, 500, 200, 200), GRASS_READY, None)
    decision_making.secondary_action = ("craft", ["Torch"])
    
    # for adding stuff to inventory
    modeling.player_model.inventory.add_item("CutGrass", 2)
    modeling.player_model.inventory.add_item("Twigs", 2)
    # modeling.player_model.inventory.add_item("Berries", 1)

    time.sleep(2)
    start = time.time()
    while time.time() - start < 20:
        control.control(decision_making, modeling)
        action.act(control)
        if control.just_finished_action:
            break
        time.sleep(0.05)
    print("done")