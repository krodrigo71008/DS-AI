import pickle

from tqdm.contrib.itertools import product
import numpy as np
import pandas as pd

from decisionMaking.DecisionMakingSimulator import DecisionMakingSimulator

if __name__ == "__main__":
    sim = DecisionMakingSimulator()
    sim.run()
        
    print("done")
