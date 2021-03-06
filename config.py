import os
# CONSTANTS

# PATHS
PATH = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(PATH, "MODELS", "stft_model.pt")
TRACED_MODEL_PATH = os.path.join(PATH, "MODELS", "CPP", "stft_model.pt")
AUDIO_OUT_FOL = os.path.join(PATH, "OUTPUT")
DATA_PATH = os.path.join(PATH, "DATA")
EMBEDDINGS_PATH = os.path.join(PATH, "EMBEDDINGS", "stft_latents.npy")
AUDIO_FOLDER = os.path.join(PATH, "INPUT")
LABEL_KEYFILE = os.path.join(PATH, "label_mapping.txt")

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
EPOCHS = 2000
LEARNING_RATE = .0001
LOG_EPOCHS = 10
CHECKPOINT_EPOCHS = 50
MAX_BETA = 100
LAMBDA = 3
MAX_GRAD_NORM = 5
CONTINUE=False
if CONTINUE == True and not os.path.exists(MODEL_PATH):
	# ensure model path exists to continue from
	raise "Model not found but CONTINUE set to True"

# USER INTERFACE
SCREEN_SIZE = 250
GUI_SIZE = 250
WINDOW_SIZE = 750
SCREEN_COLOR = (255, 255, 255)

# PARAMETERS
PARAMS = {
	"attack": {"addr": "/1/attack", "min_val": 0.001, "max_val": 1.5, "start_val": 0.1 },
	"decay": {"addr": "/1/decay", "min_val": 0.0, "max_val": 1.5, "start_val": 0.0 },
	"sustain": {"addr": "/1/sustain", "min_val": 0.0, "max_val": 1.2, "start_val": 1.0 },
	"release": {"addr": "/1/release", "min_val": 0.001, "max_val": 1.5, "start_val": 0.2 },
	"spread": {"addr": "/1/spread", "min_val": 0.0, "max_val": 1.0, "start_val": 0.0 },
	"smooth": {"addr": "/1/smooth", "min_val": 0.0, "max_val": 1.0, "start_val": 1.0 }
}

# GRANULATOR
MAX_GRAIN_HISTORY = 10
OVERLAP = 0.9
NUM_OVERLAPS = 3
TEST_BATCH_SIZE = 1 # unison of neural net input

# OSC
OSC = False
IP = "192.168.1.207"
PORT = 57121