import numpy as np
import pandas as pd
import os as os
import json
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

DIRECTORY = os.path.dirname(os.path.abspath(__file__))
with open(DIRECTORY + '/champions-vgc-stats.json', 'r') as file:
    VGC_DATA = json.load(file)
    
POKEMON_META = list(VGC_DATA['pokemon'].keys())
SIZE_OF_META = len(POKEMON_META)
POKEMON_TO_INDEX = {p: i for i, p in enumerate(POKEMON_META)}

print(POKEMON_TO_INDEX)
