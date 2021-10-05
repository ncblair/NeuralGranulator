import os

import numpy as np
from tqdm import tqdm
import torch
from torch.utils.data import TensorDataset, DataLoader
import nsgt
import soundfile as sf

from model import GrainVAE


# CONSTANTS
PATH = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(PATH, "MODELS", "grain_model2.pt")
EMBEDDINGS_OUT_FOL = os.path.join(PATH, "EMBEDDINGS")
DATA_PATH = os.path.join(PATH, "DATA", "grains.npy")
BATCH_SIZE = 16
SR = 16000
USE_CUDA = False

# Make the output folder if it doesn't exist
if (not os.path.exists(EMBEDDINGS_OUT_FOL)):
	os.makedirs(EMBEDDINGS_OUT_FOL)

# init dataset
data = np.load(DATA_PATH)

# init transform
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

# convert data to Tensorflow DataLoader
data = torch.Tensor(data)
grain_length = data.shape[1]
data = TensorDataset(data)
dataloader = DataLoader(data,
						batch_size=BATCH_SIZE,
						shuffle=False,
						num_workers=8,
						pin_memory=USE_CUDA)

# load model
model = GrainVAE(grain_length, use_cuda = USE_CUDA)
if USE_CUDA:
	device = torch.device("cuda")
else:
	device = torch.device("cpu")
model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
model.eval()
if USE_CUDA:
	model.cuda()


# Run Model on Dataset
latents = []
for x in tqdm(iter(dataloader)):
	# # Get batch (variable on GPU)
	x = x[0]
	if USE_CUDA:
		x = x.cuda()

	# encode x to get mu and std
	mu, log_var = model.encoder(x)
	std = torch.exp(log_var/2)

	# sample z from normal
	q = torch.distributions.Normal(mu, std)
	latents.append(np.array(q.sample().detach().cpu()))

latents = np.concatenate(latents)
np.save(os.path.join(EMBEDDINGS_OUT_FOL, "latents.npy"), latents)
