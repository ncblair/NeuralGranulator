import numpy as np
import os
import json

def load_data(data_path):
	if data_path.endswith(".npy"):
		x = np.load(data_path)
		y = [os.path.basename(data_path)] * x.shape[0]
		return x, y
	elif os.path.isdir(data_path):
		data = [load_data(os.path.join(data_path, d)) for d in os.listdir(data_path)]
		data = [x for x in data if x is not None]
		x, y = zip(*data)
		return np.concatenate(x), sum(y, [])


def map_labels_to_ints(labels, key_file=None):
	if key_file is not None and os.path.exists(key_file):
		with open(key_file, "r") as f:
			mapping = json.load(f)
	else:
		unique_labels = set(labels)
		mapping = {label:i for i, label in enumerate(unique_labels)}
		if key_file is not None:
			with open(key_file, "w") as f:
				json.dump(mapping, f)
	mapped = np.array([mapping[label] for label in labels])
	return mapped
