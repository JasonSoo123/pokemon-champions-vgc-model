import numpy as np
import pandas as pd
import os as os
import json
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

directory = os.path.dirname(os.path.abspath(__file__))
with open(directory + '/champions-vgc-stats.json', 'r') as file:
    vgc_data = json.load(file)
    
POKEMON_META = list(vgc_data['pokemon'].keys())
size_of_meta = len(POKEMON_META)
pokemon_to_idx = {p: i for i, p in enumerate(POKEMON_META)}

print(pokemon_to_idx)
