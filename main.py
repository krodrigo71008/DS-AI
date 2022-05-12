from action.Action import Action
from control.Control import Control
from decisionMaking.DecisionMaking import DecisionMaking
from modeling.Modeling import Modeling
from perception.Perception import Perception

import keyboard

if __name__ == "__main__":
    # press p to start the AI
    while not keyboard.is_pressed("p"):
        pass
    action = Action()
    control = Control()
    decision_making = DecisionMaking()
    modeling = Modeling()
    perception = Perception()
    # press p again to end the program
    while not keyboard.is_pressed("p"):
        objects = perception.perceive()
        modeling.update_model(objects)
        decision_making.decide(modeling)
        control.control(decision_making, modeling)
        action.act(control)
