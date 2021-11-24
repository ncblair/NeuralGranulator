import os

import numpy as np
import torch
# import nsgt
import soundfile as sf

from model import GrainVAE
from utils import load_data
from config import MODEL_PATH, AUDIO_OUT_FOL, DATA_PATH, BATCH_SIZE, SR, USE_CUDA

# Get grain
grain = load_data(DATA_PATH)[0][0]
# Prepare inverse NSGT transform
# scale = nsgt.MelScale(20, 22050, 24)
# transform = nsgt.NSGT(scale, SR, len(grain), real=True, matrixform=True, reducedform=False)
# example_nsgt = transform.forward(grain)
# nsgt_shape = np.array(example_nsgt).shape
# # get grain length
# nsgt_length = nsgt_shape[0] * nsgt_shape[1] * 2 # times 2 for complex number

# load model
model = GrainVAE(grain.shape[0], use_cuda = USE_CUDA)
if USE_CUDA:
	device = torch.device("cuda")
else:
	device = torch.device("cpu")
model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
model.eval()
if USE_CUDA:
	model.cuda()

# get random latent vector
mean = torch.zeros(BATCH_SIZE, model.l_dim)
mean[:, 0] = 3
std = torch.ones(BATCH_SIZE, model.l_dim)
latent_vector = torch.distributions.Normal(mean, std).sample()

if USE_CUDA:
	latent_vector.cuda()

# get model nsgt out
model_out = model.forward(latent_vector).detach().cpu().numpy()

# put output of model back into complex domain
# complex_out = model.to_complex_repr(model_out)

# write each output in batch separately to file
for i in range(BATCH_SIZE):

	# put output of model into format usable by nsgt
	audio_out = model_out[i:i+1].T
	# audio_out = audio_out.reshape(nsgt_shape[0], nsgt_shape[1])
	# audio_out = list(audio_out)

	# transform output from nsgt to audio
	# audio_out = transform.backward(audio_out)

	# write to file
	file_out = os.path.join(AUDIO_OUT_FOL, f"generated_{i:0>3d}.wav")
	sf.write(file_out, audio_out, SR, format="WAV") 