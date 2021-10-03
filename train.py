import os

import numpy as np
from tqdm import tqdm
import torch
import torch.optim as optim
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable
from torch.utils.data import TensorDataset, DataLoader
import nsgt

from model import GrainVAE

# CONSTANTS
PATH = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(PATH, "DATA", "grains.npy")
MODEL_PATH = os.path.join(PATH, "MODELS", "grain_model.pt")
EPOCHS = 1000
BATCH_SIZE = 16
SR = 16000
DTYPE = torch.cuda.FloatTensor

# init dataset
data = np.load(DATA_PATH)
scale = nsgt.MelScale(20, 22050, 24)
transform = nsgt.NSGT(scale, SR, data.shape[1], real=True, matrixform=True, reducedform=False)

#preprocessing step
data_temp = []
for grain in data:
	data_transformed = transform.forward(grain)
	data_transformed = np.array(data_transformed).flatten()
	data_real = data_transformed.real
	data_imag = data_transformed.imag
	data_temp.append(np.concatenate([data_real, data_imag]))
data = np.array(data_temp)

#convert data to Tensorflow DataLoader
data = torch.Tensor(data)
grain_length = data.shape[1]
data = TensorDataset(data)
dataloader = DataLoader(data,
						batch_size=BATCH_SIZE,
						shuffle=True,
						num_workers=8,
						pin_memory=True)

# init model
model = GrainVAE(grain_length)
model.train()
model.cuda()

# init optimizer
optimizer = optim.Adam(model.parameters(), lr=0.001)

# TRAIN LOOP
for epoch in tqdm(range(EPOCHS)):

	# Go through batches
	for x in iter(dataloader):
		# # Get batch (variable on GPU)
		# x = Variable(data[i: i + BATCH_SIZE])
		x = Variable(x[0]).type(DTYPE)
		
		# Run model
		loss = model.train_step(x)

		# Optimize model
		optimizer.zero_grad()
		loss.backward()
		loss = loss.data

		#CONSIDER IMPLEMENTING GRADIENT CLIPPING HERE (LOOK THAT UP)

		#LOG TRAINING HERE

# Save model
torch.save(model, MODEL_PATH)