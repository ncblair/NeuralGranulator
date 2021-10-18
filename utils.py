import numpy as np
import os

def load_data(data_path):
	if data_path.endswith(".npy"):
		return np.load(data_path)
	elif os.path.isdir(data_path):
		data = [load_data(os.path.join(data_path, d)) for d in os.listdir(data_path)]
		data = [x for x in data if x is not None]
		return np.concatenate(data)

