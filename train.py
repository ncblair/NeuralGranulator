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
from utils import load_data, map_labels_to_ints
from config import  DATA_PATH, MODEL_PATH, CONTINUE, EPOCHS, BATCH_SIZE, LEARNING_RATE, \
					LAMBDA, MAX_GRAD_NORM, SR, LOG_EPOCHS, MAX_BETA, USE_CUDA, LABEL_KEYFILE, \
					CHECKPOINT_EPOCHS

if USE_CUDA:
	DTYPE = torch.cuda.FloatTensor
else:
	DTYPE = torch.FloatTensor

if CONTINUE:
	warmup_period = 0
else:
	warmup_period = EPOCHS/2

# init dataset
X, Y = load_data(DATA_PATH)
Y = map_labels_to_ints(Y, key_file=LABEL_KEYFILE)

print("LOADED DATASET: ", X.shape)
scale = nsgt.MelScale(20, 22050, 24)
transform = nsgt.NSGT(scale, SR, X.shape[1], real=True, matrixform=True, reducedform=False)
#preprocessing step
data_temp = []
for grain in tqdm(X, "PREPROCESSING"):
	data_transformed = transform.forward(grain)
	data_transformed = np.array(data_transformed).flatten()
	data_real = data_transformed.real
	data_imag = data_transformed.imag
	data_temp.append(np.concatenate([data_real, data_imag]))
X = np.array(data_temp)

# convert data to Tensorflow DataLoader
X = torch.Tensor(X)
Y = torch.Tensor(Y).long()
grain_length = X.shape[1]

data = TensorDataset(X, Y)
dataloader = DataLoader(data,
						batch_size=BATCH_SIZE,
						shuffle=True,
						num_workers=8,
						pin_memory=True)

# init model
model = GrainVAE(grain_length, use_cuda = USE_CUDA)
if USE_CUDA:
	device = torch.device("cuda")
else:
	device = torch.device("cpu")

if CONTINUE:
	model.load_state_dict(torch.load(MODEL_PATH, map_location=device))

model.train()

if USE_CUDA:
	model.cuda()

# init optimizer
optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

# TRAIN LOOP
losses, kls, recons = [], [], []
pbar = tqdm(range(EPOCHS))
for epoch in pbar:

	# Get Beta regularizer (increase linearly from 0 to max_beta during warmup_period)
	beta = (epoch / EPOCHS) * MAX_BETA if epoch < warmup_period else MAX_BETA

	# Go through batches
	for x, y in iter(dataloader):
		# # Get batch (variable on GPU)
		# x = Variable(data[i: i + BATCH_SIZE])
		x = Variable(x).type(DTYPE)
		y.type(DTYPE)
		# Run model
		loss, kl, recon = model.train_step(x, beta, y, lmbda=LAMBDA)

		# Optimize model
		optimizer.zero_grad()
		loss.backward()
		loss = loss.data
		losses += [loss.detach().cpu()]
		kls += [kl.detach().cpu()]
		recons += [recon.detach().cpu()]
		if len(losses) > LOG_EPOCHS:
			losses = losses[1:]
			kls = kls[1:]
			recons = recons[1:]

		# Clip gradients and take optimization step
		torch.nn.utils.clip_grad_norm_(model.parameters, MAX_GRAD_NORM)
		optimizer.step()

		#LOG TRAINING HERE
	pbar.set_description(f"Loss: {np.mean(losses)}, recon: {np.mean(recons)}, kls: {np.mean(kls)}")

	if epoch % CHECKPOINT_EPOCHS == 0 and epoch > 0:
		torch.save(model.state_dict(), MODEL_PATH)

# Save model
torch.save(model.state_dict(), MODEL_PATH)