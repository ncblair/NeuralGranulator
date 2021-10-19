import os

import numpy as np
from tqdm import tqdm
import torch
from torch.utils.data import TensorDataset, DataLoader
import nsgt
import soundfile as sf

from model import GrainVAE
from utils import load_data, map_labels_to_ints

from config import MODEL_PATH, EMBEDDINGS_PATH, DATA_PATH, BATCH_SIZE, SR, USE_CUDA, LABEL_KEYFILE



# Make the output folder if it doesn't exist
embed_fol = os.path.dirname(EMBEDDINGS_PATH)
if (not os.path.exists(embed_fol)):
	os.makedirs(embed_fol)

# init dataset
data, Y = load_data(DATA_PATH)
Y = map_labels_to_ints(Y, key_file=LABEL_KEYFILE)

# init transform
scale = nsgt.MelScale(20, 22050, 24)
transform = nsgt.NSGT(scale, SR, data.shape[1], real=True, matrixform=True, reducedform=False)

#preprocessing step
data_temp = []
for grain in tqdm(data, "PREPROCESSING"):
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
	if USE_CUDA:
		x = x[0].cuda()

	# encode x to get mu and std
	mu, log_var = model.encoder(x)
	# std = torch.exp(log_var/2)

	# # sample z from normal
	# q = torch.distributions.Normal(mu, std)
	# latents.append(np.array(q.sample().detach().cpu()))

	# at test time, just return mu
	latents.append(mu.detach().cpu().numpy())

latents = np.concatenate(latents)
np.save(EMBEDDINGS_PATH, latents)
y_path = EMBEDDINGS_PATH[:-4] + "_y" + ".npy"
np.save(y_path, Y)
