import math
import asyncio

import pygame
from sklearn.decomposition import PCA
import numpy as np
import nsgt
import torch #1.2.0
import soundfile as sf
import colorsys
from scipy.ndimage.filters import gaussian_filter
import matplotlib.pyplot as plt

from model import GrainVAE
from granulator import Granulator
from utils import load_data
from gui import Knob
from config import 	MODEL_PATH, EMBEDDINGS_PATH, DATA_PATH, SCREEN_SIZE, \
					WINDOW_SIZE, SCREEN_COLOR, USE_CUDA, SR, BIT_WIDTH, \
					CHANNELS, TEST_BATCH_SIZE, SPREAD, OSC, LAMBDA, GUI_SIZE


# Conditionally Import OSC:
osc_str = input("Would you like to use OSC for traversing through latent space? (y/N)")
if osc_str == 'y' or osc_str=='Y':
	OSC = True
	import osc_latent

# Get latent data
latent_data, latent_y = np.load(EMBEDDINGS_PATH), np.load(EMBEDDINGS_PATH[:-4] + "_y" + ".npy")
latent_dim = latent_data.shape[1]
num_classes = len(set(latent_y))

# Get PCA embedding
pca = PCA(n_components=2, whiten=True)
pca.fit(latent_data)
class_vectors = np.eye(latent_dim)[:num_classes] * LAMBDA
projections = pca.transform(class_vectors)
# c_dict = {0:"red", 1:"blue", 2:"green"}
# colors = [c_dict[i] for i in latent_y]
# plt.scatter(projections[:, 0], projections[:, 1], c=colors)
# # plt.xlim([-0.01, 0.01])
# # plt.ylim([-0.01, 0.01])
# plt.show()
# import pdb;pdb.set_trace()


# Prepare inverse NSGT transform
grain = load_data(DATA_PATH)[0][0]
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
pygame.font.init()
font = pygame.font.SysFont('arial', 30)

# Init Granulator
gran = Granulator()
gran.replace_grain(np.zeros(grain_length))
gran.init_audio_stream(SR, BIT_WIDTH, CHANNELS)
gran.init_midi()

# Set up the drawing window
win = pygame.display.set_mode([2*WINDOW_SIZE, WINDOW_SIZE])
screen = pygame.Surface((SCREEN_SIZE, SCREEN_SIZE))
gui = pygame.Surface((GUI_SIZE, GUI_SIZE))

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
		z = z.cuda()
		z_mean = z_mean.cuda()
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


def draw_background_circles(z, sceren):
	"""
	visualize the latent space as HUE
	z: latent vector
	"""
	saturation = 1
	value = 1
	sqrt_num_circles = int(math.sqrt(latent_dim))
	z = z.cpu().numpy()[0]
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

def distort(surface, screen, blur = .25):
	imgdata = pygame.surfarray.array3d(surface)
	# noisy = imgdata - np.random.rand(*imgdata.shape) * 50
	# noisy = np.clip(noisy, 0, 255)
	blurred = gaussian_filter(imgdata, sigma=(3, 3, 0))
	distorted = pygame.surfarray.make_surface(blurred)

	surface.blit(distorted, (0, 0))

def draw_latent_projections(projections, window):
	saturation = 1
	value = 1

	text_and_rects = []
	for i, position in enumerate(projections):
		# print(position, SCREEN_SIZE)
		position = (position + 3) * SCREEN_SIZE / 6 # screen goes from coordinates -3 to 3

		hue = i / num_classes
		color = np.array(colorsys.hsv_to_rgb(hue,saturation,value))
		color = list((255*color).astype(np.int))
		pygame.draw.circle(screen, color, position, 1)
		text = font.render(f"{i}", True, (0, 0, 0))
		textRect = text.get_rect()
		textRect.center = position * WINDOW_SIZE / SCREEN_SIZE
		window.blit(text, textRect)


# GUI

# Run PyGame Loop
async def main_loop():

	gran.start_audio_stream()

	circle_pos = np.array([SCREEN_SIZE/2, SCREEN_SIZE/2])
	z_mean, z = get_latent_vector(circle_pos, SPREAD)
	update_audio(z)
	coords = np.zeros(2)
	old_coords = np.zeros(2)
	
	is_gui_element_active = False
	knobs = {"attack":Knob(gui,100,50,100,100,(0,0,0),(255,0,0),0.0,1.0, 0.5), 
			"decay":Knob(gui,200,50,100,100,(0,0,0),(255,0,0),0.0,1.0, 0.5),
			"release":Knob(gui,100,150,100,100,(0,0,0),(255,0,0),0.0,1.0, 0.5),
			"sustain":Knob(gui,200,150,100,100,(0,0,0),(255,0,0),0.0,1.0, 0.5),
			"variance":Knob(gui,300,50,100,100,(0,0,0),(255,0,0),0.0,1.0, 0.5)}

	# Run PyGame Loop
	running = True
	while running:
		# get mouse position in [0, 1]
		mouse_pos = pygame.mouse.get_pos()
		if OSC:
			old_coords = coords
			coords = osc_latent.osc_handler.get_osc_coordinates() * SCREEN_SIZE
		else:
			coords = np.array(mouse_pos) * SCREEN_SIZE / WINDOW_SIZE

		gui_coords = (np.array(mouse_pos) - np.array([WINDOW_SIZE, 0])) * GUI_SIZE / WINDOW_SIZE

		# draw
		screen.fill(SCREEN_COLOR)
		gui.fill(SCREEN_COLOR)
		draw_background_circles(z_mean, screen)
		# distort(screen, screen)
		pygame.draw.circle(screen, (0,0,0), circle_pos, (SCREEN_SIZE/50))

		# Did the user click the window close button?
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False

			# On Mouse Button Up
			if event.type == pygame.MOUSEBUTTONUP:
				z_mean, z = get_latent_vector(circle_pos, SPREAD)
				update_audio(z)
				is_mouse_down = False

		is_a_knob_active = False
		for knob_name in knobs:
			knob = knobs[knob_name]
			is_a_knob_active = knob.draw(gui_coords, pygame.mouse.get_pressed(), \
				not is_gui_element_active) or is_a_knob_active
		is_gui_element_active = is_a_knob_active

		if len([ 1 for knob_name in knobs \
			if knobs[knob_name].cur_val != knobs[knob_name].old_val]) \
				> 0 :
			gran.set_envs(knobs["attack"].cur_val,knobs["decay"].cur_val, \
				knobs["sustain"].cur_val, knobs["release"].cur_val)

		# If mouse being pressed
		if OSC:
			if not np.array_equal(coords, old_coords):
				circle_pos = coords
				z_mean, z = get_latent_vector(circle_pos, SPREAD)
				update_audio(z)
		else:
			if pygame.mouse.get_pressed()[0]:
				circle_pos = coords
				z_mean, z = get_latent_vector(circle_pos, SPREAD)
				update_audio(z)

		transformed_screen = pygame.transform.scale(screen,(WINDOW_SIZE, WINDOW_SIZE))
		transformed_gui = pygame.transform.scale(gui, (WINDOW_SIZE, WINDOW_SIZE))
		win.blit(transformed_screen, (0, 0))
		win.blit(transformed_gui, (WINDOW_SIZE, 0))
		draw_latent_projections(projections, win)
		
			
		pygame.display.flip()
		await asyncio.sleep(0)

	# Done! Time to quit.
	pygame.quit()

if OSC:
	async def init_osc_latent():
		server = osc_latent.osc_server.AsyncIOOSCUDPServer(
				(osc_latent.IP, osc_latent.PORT), osc_latent.dispatcher,
				asyncio.get_event_loop())
		transport, protocol = await server.create_serve_endpoint()
		await main_loop()
		transport.close()
	asyncio.run(init_osc_latent())
else :
	asyncio.run(main_loop())