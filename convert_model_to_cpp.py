import numpy as np
#import nsgt
import torch #1.2.0
import os
from model import GrainVAE
from utils import load_data
from config import 	USE_CUDA, MODEL_PATH, DATA_PATH, EMBEDDINGS_PATH, TRACED_MODEL_PATH, SR

# Get latent data
latent_data, latent_y = np.load(EMBEDDINGS_PATH), np.load(EMBEDDINGS_PATH[:-4] + "_y" + ".npy")
latent_dim = latent_data.shape[1]
num_classes = len(set(latent_y))

# Prepare inverse NSGT transform
grain = load_data(DATA_PATH)[0][0]
grain_length = len(grain)
# scale = nsgt.MelScale(20, 22050, 24)
# transform = nsgt.NSGT(scale, SR, grain_length, real=True, matrixform=True, reducedform=False)
# example_nsgt = transform.forward(grain)
# nsgt_shape = np.array(example_nsgt).shape
# nsgt_length = nsgt_shape[0] * nsgt_shape[1] * 2 # times 2 for complex number


# Load Model
model = GrainVAE(grain_length, use_cuda = USE_CUDA)
if USE_CUDA:
	device = torch.device("cuda")
else:
	device = torch.device("cpu")
model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
model.eval()

if USE_CUDA:
	model.cuda()

# get trace scripted module
example_input = torch.Tensor(latent_data[:1])
with torch.no_grad():
	if USE_CUDA:
		example_input.cuda()
	traced_script_module = torch.jit.trace(model, example_input)

	if not os.path.exists(TRACED_MODEL_PATH):
		os.makedirs(os.path.basename(TRACED_MODEL_PATH))
	# serialize trace scripted model
	traced_script_module.save(TRACED_MODEL_PATH)