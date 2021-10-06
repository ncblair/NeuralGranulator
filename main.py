import os
import math

import pygame
import pygame.midi
from sklearn.decomposition import PCA
import numpy as np
import nsgt
import torch
import soundfile as sf
import pyaudio
import colorsys
from scipy.ndimage.filters import gaussian_filter

from model import GrainVAE
from granulator import Granulator

PATH = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(PATH, "MODELS", "grain_model2.pt")
EMBEDDINGS_PATH = os.path.join(PATH, "EMBEDDINGS", "latents.npy")
DATA_PATH = os.path.join(PATH, "DATA", "grains.npy")
SCREEN_SIZE = 250
WINDOW_SIZE = 750
SCREEN_COLOR = (255, 255, 255)
USE_CUDA = False
SR = 16000
BIT_WIDTH = 4

# Get latent data
latent_data = np.load(EMBEDDINGS_PATH)
latent_dim = latent_data.shape[1]

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
win = pygame.display.set_mode([WINDOW_SIZE, WINDOW_SIZE])
screen = pygame.Surface((SCREEN_SIZE, SCREEN_SIZE))

circle_pos = (SCREEN_SIZE/2, SCREEN_SIZE/2)
circle_size = SCREEN_SIZE/50
# circle_size = circle_size_mean
# circle_size_variance = SCREEN_SIZE / 400
z = torch.zeros(1, latent_dim)

# Init Granulator
gran = Granulator()
gran.replace_grain(np.zeros(grain_length))
gran.init_audio_stream(SR, BIT_WIDTH)
gran.start_audio_stream()
gran.init_midi()

def get_latent_vector(pos):
	# get corresponding latent vector
	pos = (pos * 6 / SCREEN_SIZE) - 3
	z = pca.inverse_transform(np.expand_dims(pos, 0))
	z = torch.Tensor(z)
	if USE_CUDA:
		z.cuda()
	return z

def update_audio(z):
	# get model nsgt out
	model_out = model.decoder(z)
	complex_out = model.to_complex_repr(model_out)
	nsgt_out = list(complex_out.reshape(nsgt_shape[0], nsgt_shape[1]))

	# get audio from nsgt inverse transform
	audio_out = transform.backward(nsgt_out) 

	# normalize audio to help prevent clipping
	audio_out = audio_out / np.max(np.abs(audio_out))
	gran.replace_grain(audio_out)

def draw_background_circles(z):
	"""
	visualize the latent space as HUE
	z: latent vector
	"""
	saturation = 1
	value = 1
	sqrt_num_circles = int(math.sqrt(latent_dim))
	z = z.numpy()[0]
	min_z = np.min(z)
	max_z = np.max(z)
	if min_z != max_z: # avoid divide by zero
		z = (z - min_z) / (max_z - min_z) # normalize z
	for i in range(sqrt_num_circles):
		for j in range(sqrt_num_circles):
			position = (SCREEN_SIZE / 2 + np.array([i, j]) * SCREEN_SIZE)
			position = position / (sqrt_num_circles)
			hue = z[i*sqrt_num_circles + j]
			color = np.array(colorsys.hsv_to_rgb(hue,saturation,value))
			color = list((255*color).astype(np.int))
			size = circle_size # + np.random.rand()*circle_size_variance
			pygame.draw.circle(screen, color, position, size)

def distort(surface, blur = .25):
	imgdata = pygame.surfarray.array3d(surface)
	# noisy = imgdata - np.random.rand(*imgdata.shape) * 50
	# noisy = np.clip(noisy, 0, 255)
	blurred = gaussian_filter(imgdata, sigma=(3, 3, 0))
	distorted = pygame.surfarray.make_surface(blurred)

	surface.blit(distorted, (0, 0))

# Start Audio
circle_pos = np.array([SCREEN_SIZE/2, SCREEN_SIZE/2])
z = get_latent_vector(circle_pos)
update_audio(z)

# Run PyGame Loop
running = True
while running:
	# get mouse position in [0, 1]
	mouse_pos = np.array(pygame.mouse.get_pos()) * SCREEN_SIZE / WINDOW_SIZE

	# draw
	screen.fill(SCREEN_COLOR)
	draw_background_circles(z)
	distort(screen)
	pygame.draw.circle(screen, (0,0,0), circle_pos, (SCREEN_SIZE/50))
	# Did the user click the window close button?
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			running = False

		# On Mouse Button Up
		if event.type == pygame.MOUSEBUTTONUP:
			z = get_latent_vector(circle_pos)
			update_audio(z)

	# If mouse being pressed
	if pygame.mouse.get_pressed()[0]:
		circle_pos = mouse_pos
		z = get_latent_vector(circle_pos)
		update_audio(z)


	# # if midi in
	if gran.midi_input is not None and gran.midi_input.poll():
		# if event.type == pygame.midi.MIDIIN:
		midi_events = gran.midi_input.read(10)
		# convert them into pygame events.
		midi_evs = pygame.midi.midis2events(midi_events, gran.midi_input.device_id)

		for m_e in midi_evs:
			if m_e.status == 144:
				note = m_e.data1
				gran.note_on(note)

			if m_e.status == 128:
				note = m_e.data1
				gran.note_off(note)


	transformed_screen = pygame.transform.scale(screen,(WINDOW_SIZE, WINDOW_SIZE))
	win.blit(transformed_screen, (0, 0))
		
	pygame.display.flip()


gran.close_audio_stream()

# Done! Time to quit.
pygame.quit()