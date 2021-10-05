import os

import pygame
from sklearn.decomposition import PCA
import numpy as np
import nsgt
import torch
import soundfile as sf
import pyaudio

from model import GrainVAE
from granulator import Granulator

PATH = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(PATH, "MODELS", "grain_model2.pt")
EMBEDDINGS_PATH = os.path.join(PATH, "EMBEDDINGS", "latents.npy")
DATA_PATH = os.path.join(PATH, "DATA", "grains.npy")
SCREEN_SIZE = 500
SCREEN_COLOR = (255, 255, 255)
USE_CUDA = False
SR = 16000
BIT_WIDTH = 4

# Get latent data
latent_data = np.load(EMBEDDINGS_PATH)

# Get PCA embedding
pca = PCA(n_components=2, whiten=True)
pca.fit(latent_data)

# Prepare inverse NSGT transform
grain = np.load(DATA_PATH)[0]
grain_length = len(grain)
scale = nsgt.MelScale(20, 22050, 24)
transform = nsgt.NSGT(scale, SR, len(grain), real=True, matrixform=True, reducedform=False)
example_nsgt = transform.forward(grain)
nsgt_shape = np.array(example_nsgt).shape
nsgt_length = nsgt_shape[0] * nsgt_shape[1] * 2 # times 2 for complex number

# Load Model
model = GrainVAE(nsgt_length, use_cuda = USE_CUDA)
if USE_CUDA:
	device = torch.device("cuda")
else:
	device = torch.device("cpu")
model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
model.eval()
if USE_CUDA:
	model.cuda()

# Initialize PyGame
pygame.init()

# Set up the drawing window
screen = pygame.display.set_mode([SCREEN_SIZE, SCREEN_SIZE])
screen.fill(SCREEN_COLOR)
pygame.display.flip()

# Init Granulator
gran = Granulator()
gran.replace_grain(np.zeros(grain_length))
gran.init_audio_stream(SR, BIT_WIDTH)
gran.start_audio_stream()

# Run PyGame Loop
running = True
while running:

	# Did the user click the window close button?
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			running = False

		# On Mouse Button Up
		if event.type == pygame.MOUSEBUTTONUP:
			# Get Corresponding Latent Vector
			mouse_pos = -2 + np.array(pygame.mouse.get_pos())*4/SCREEN_SIZE
			z = pca.inverse_transform(np.expand_dims(mouse_pos, 0))
			z = torch.Tensor(z)
			if USE_CUDA:
				z.cuda()

			# get model nsgt out
			model_out = model.decoder(z)
			complex_out = model.to_complex_repr(model_out)
			nsgt_out = list(complex_out.reshape(nsgt_shape[0], nsgt_shape[1]))

			# get audio from nsgt inverse transform
			audio_out = transform.backward(nsgt_out)
			gran.replace_grain(audio_out)

gran.close_audio_stream()

# Done! Time to quit.
pygame.quit()