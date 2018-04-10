import pandas as pd
import numpy as np

states = ["increase", "decrease", "stable"]
actions = ["buy", "sell", "wait"]
table = pd.DataFrame(index=states, columns=actions, data=np.zeros((len(states), len(actions))))
print("table loc: ", table.loc["increase"])
print("table loc2: ", table.loc["increase", :])
print("table loc max: ", table.loc["increase", :].max())
print("table loc idxmax: ", table.loc["increase", :].idxmax())