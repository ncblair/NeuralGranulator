import os
# CONSTANTS

# PATHS
PATH = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(PATH, "MODELS", "grain_model_lambda.pt")
AUDIO_OUT_FOL = os.path.join(PATH, "OUTPUT")
DATA_PATH = os.path.join(PATH, "DATA", "nsynth", "mini")
EMBEDDINGS_PATH = os.path.join(PATH, "EMBEDDINGS", "latents2.npy")
AUDIO_FOLDER = os.path.join(PATH, "INPUT")
LABEL_KEYFILE = os.path.join(PATH, "label_mapping.txt")

# DATA CONSTANTS
BATCH_SIZE = 1024
SR = 16000
BIT_WIDTH = 4 # Number of bytes in a sample, 1, 2, 3, or 4, 4 = 32bit
CHANNELS = 1

# CUDA
USE_CUDA = True

# DATA GENERATION
SILENCE_CUTOFF = 0.05


# TRAINING
EPOCHS = 600
LEARNING_RATE = .0001
LOG_EPOCHS = 10
CHECKPOINT_EPOCHS = 50
MAX_BETA = 50
LAMBDA = 3
MAX_GRAD_NORM = 5
CONTINUE=False
if CONTINUE == True and not os.path.exists(MODEL_PATH):
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


# OSC
OSC = False
IP = "192.168.1.207"
PORT = 57121