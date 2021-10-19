import os
# CONSTANTS

# PATHS
PATH = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(PATH, "MODELS", "grain_model_conditional.pt")
AUDIO_OUT_FOL = os.path.join(PATH, "OUTPUT")
DATA_PATH = os.path.join(PATH, "DATA")
EMBEDDINGS_PATH = os.path.join(PATH, "EMBEDDINGS", "latents.npy")
AUDIO_FOLDER = os.path.join(PATH, "INPUT")

# DATA CONSTANTS
BATCH_SIZE = 1024
SR = 16000
BIT_WIDTH = 4 # Number of bytes in a sample, 1, 2, 3, or 4, 4 = 32bit
CHANNELS = 1

# CUDA
USE_CUDA = False

# DATA GENERATION
SILENCE_CUTOFF = 0.05

# TRAINING
EPOCHS = 1000
LOG_EPOCHS = 10
MAX_BETA = 2.0
CONTINUE=False
if not os.path.exists(MODEL_PATH):
	# ensure model path exists to continue from
	raise "Model not found but CONTINUE set to True"

# USER INTERFACE
SCREEN_SIZE = 250
WINDOW_SIZE = 750
SCREEN_COLOR = (255, 255, 255)

# GRANULATOR
MAX_GRAIN_HISTORY = 10
OVERLAP = 0.9
NUM_OVERLAPS = 3
TEST_BATCH_SIZE = 1 # unison of neural net input
SPREAD = 0 # variance of neural net input


