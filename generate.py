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
AUDIO_OUT_PATH = os.path.join(PATH, "AUDIO", "generated_audio.wav")
DATA_PATH = os.path.join(PATH, "DATA", "grains.npy")
EPOCHS = 10
BATCH_SIZE = 16
SR = 16000


# load model
model = torch.load(MODEL_PATH)
model.eval()

# get random latent vector
zeros = torch.zeros(1, model.l_dim)
ones = torch.ones(1, model.l_dim)
latent_vector = torch.distributions.Normal(zeros, ones).rsample().cuda()

# get model nsgt out
model_out = model.decoder(latent_vector)

# post-process nsgt back to audio
scale = nsgt.MelScale(20, 22050, 24)
grain = np.load(DATA_PATH)[0]
transform = nsgt.NSGT(scale, SR, len(grain), real=True, matrixform=True, reducedform=False)
model_out = model_out.cpu().detach().numpy()
complex_out = np.zeros((1, model_out.shape[1]//2)).astype(np.cdouble)
complex_out.real = model_out[:, :model_out.shape[1]//2]
complex_out.imag = model_out[:, model_out.shape[1]//2:]

example_nsgt = transform.forward(grain)

nsgt_shape = np.array(example_nsgt).shape
complex_out = complex_out.reshape(nsgt_shape[0], nsgt_shape[1])
complex_out = list(complex_out)
example_out = transform.backward(example_nsgt)
audio_out = transform.backward(complex_out)

sf.write(AUDIO_OUT_PATH, audio_out, SR, "PCM_32") 