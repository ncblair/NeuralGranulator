import os

import numpy as np
from tqdm import tqdm
import torch
import torch.nn as nn
import torch.nn.functional as F
import nsgt
import soundfile as sf

from model import GrainVAE

# CONSTANTS
PATH = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(PATH, "MODELS", "grain_model.pt")
AUDIO_OUT_FOL = os.path.join(PATH, "OUTPUT")
DATA_PATH = os.path.join(PATH, "DATA", "grains.npy")
EPOCHS = 10
BATCH_SIZE = 16
SR = 16000


# load model
model = torch.load(MODEL_PATH)
model.eval()

# get random latent vector
zeros = torch.zeros(BATCH_SIZE, model.l_dim)
ones = torch.ones(BATCH_SIZE, model.l_dim)
latent_vector = torch.distributions.Normal(zeros, ones).rsample().cuda()

# get model nsgt out
model_out = model.decoder(latent_vector)

# Prepare inverse NSGT transform
scale = nsgt.MelScale(20, 22050, 24)
grain = np.load(DATA_PATH)[0]
transform = nsgt.NSGT(scale, SR, len(grain), real=True, matrixform=True, reducedform=False)
example_nsgt = transform.forward(grain)
nsgt_shape = np.array(example_nsgt).shape

# put output of model back into complex domain
model_out = model_out.cpu().detach().numpy()
complex_out = np.zeros((BATCH_SIZE, model_out.shape[1]//2)).astype(np.cdouble)
complex_out.real = model_out[:, :model_out.shape[1]//2]
complex_out.imag = model_out[:, model_out.shape[1]//2:]

# write each output in batch separately to file
for i in range(BATCH_SIZE):

	# put output of model into format usable by nsgt
	audio_out = complex_out[i:i+1]
	audio_out = audio_out.reshape(nsgt_shape[0], nsgt_shape[1])
	audio_out = list(audio_out)

	# transform output from nsgt to audio
	audio_out = transform.backward(audio_out)

	# write to file
	file_out = os.path.join(AUDIO_OUT_FOL, f"generated_{i:0>3d}.wav")
	sf.write(file_out, audio_out, SR, "PCM_32") 