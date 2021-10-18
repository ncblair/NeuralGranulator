import math

import pygame
from sklearn.decomposition import PCA
import numpy as np
import nsgt
import torch #1.2.0
import soundfile as sf
import colorsys
from scipy.ndimage.filters import gaussian_filter
from model import GrainVAE
from granulator import Granulator
from utils import load_data
from config import 	MODEL_PATH, EMBEDDINGS_PATH, DATA_PATH, SCREEN_SIZE, \
					WINDOW_SIZE, SCREEN_COLOR, USE_CUDA, SR, BIT_WIDTH, \
					CHANNELS, TEST_BATCH_SIZE, SPREAD


# Get latent data
latent_data = load_data(EMBEDDINGS_PATH)
latent_dim = latent_data.shape[1]

# Get PCA embedding
pca = PCA(n_components=2, whiten=True)
pca.fit(latent_data)

# Prepare inverse NSGT transform
grain = load_data(DATA_PATH)[0]
grain_length = len(grain)
scale = nsgt.MelScale(20, 22050, 24)
transform = nsgt.NSGT(scale, SR, grain_length, real=True, matrixform=True, reducedform=False)
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

# Init Granulator
gran = Granulator()
gran.replace_grain(np.zeros(grain_length))
gran.init_audio_stream(SR, BIT_WIDTH, CHANNELS)
gran.init_midi()

# Set up the drawing window
win = pygame.display.set_mode([WINDOW_SIZE, WINDOW_SIZE])
screen = pygame.Surface((SCREEN_SIZE, SCREEN_SIZE))

circle_pos = (SCREEN_SIZE/2, SCREEN_SIZE/2)
circle_size = SCREEN_SIZE/50
# circle_size = circle_size_mean
# circle_size_variance = SCREEN_SIZE / 400
z = torch.zeros(1, latent_dim)

def get_latent_vector(pos, variance = 0):
	# get corresponding latent vector
	pos = (pos * 6 / SCREEN_SIZE) - 3
	z_mean = pca.inverse_transform(np.expand_dims(pos, 0))
	z_mean = torch.Tensor(z_mean)
	# get batch around that latent vector with variance
	z = z_mean + variance * torch.randn(TEST_BATCH_SIZE, latent_dim)
	if USE_CUDA:
		z.cuda()
		z_mean.cuda()
	return z_mean, z

def update_audio(z):
	# get model nsgt out
	model_out = model.decoder(z)
	complex_out = model.to_complex_repr(model_out)
	nsgts_out = [list(x.reshape(nsgt_shape[0], nsgt_shape[1])) for x in complex_out]

	# get audio from nsgt inverse transform batch and sum voices
	audio_out = np.sum([transform.backward(nsgt) for nsgt in nsgts_out], axis=0)

	# normalize audio to help prevent clipping
	audio_out = audio_out / np.max(np.abs(audio_out)) / 4

	# replace current grain in granulator
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
gran.start_audio_stream()

circle_pos = np.array([SCREEN_SIZE/2, SCREEN_SIZE/2])
z_mean, z = get_latent_vector(circle_pos, SPREAD)
update_audio(z)

# Run PyGame Loop
running = True
while running:
	# get mouse position in [0, 1]
	mouse_pos = np.array(pygame.mouse.get_pos()) * SCREEN_SIZE / WINDOW_SIZE

	# draw
	screen.fill(SCREEN_COLOR)
	draw_background_circles(z_mean)
	distort(screen)
	pygame.draw.circle(screen, (0,0,0), circle_pos, (SCREEN_SIZE/50))
	# Did the user click the window close button?
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			running = False

		# On Mouse Button Up
		if event.type == pygame.MOUSEBUTTONUP:
			z_mean, z = get_latent_vector(circle_pos, SPREAD)
			update_audio(z)

	# If mouse being pressed
	if pygame.mouse.get_pressed()[0]:
		circle_pos = mouse_pos
		z_mean, z = get_latent_vector(circle_pos, SPREAD)
		update_audio(z)

	transformed_screen = pygame.transform.scale(screen,(WINDOW_SIZE, WINDOW_SIZE))
	win.blit(transformed_screen, (0, 0))
		
	pygame.display.flip()

# Done! Time to quit.
pygame.quit()