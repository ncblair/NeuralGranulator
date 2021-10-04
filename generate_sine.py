#Generate Grains from an audio file

import os

import numpy as np
import librosa
import soundfile as sf

PATH = os.path.dirname(os.path.abspath(__file__))
AUDIO_FOLDER = os.path.join(PATH, "INPUT")
OUTPUT_FOLDER = os.path.join(PATH, "DATA")


SR = 16000 #khz
GRAIN_LEN = int(0.1 * SR) # samples
DATASET_SIZE = 10000 # 100,000 sine waves
MAX_FREQ = 20000 # hz
MIN_FREQ = 20 # hz

# make output folder if it doesn't exist
if (not os.path.exists(OUTPUT_FOLDER)):
	os.makedirs(OUTPUT_FOLDER)

# generate sine array
samples = np.linspace(0, GRAIN_LEN, GRAIN_LEN, endpoint=False)
freq = np.random.random(DATASET_SIZE)*(MAX_FREQ - MIN_FREQ) + MIN_FREQ
sines = np.sin(2 * np.pi * np.outer(freq, samples))


# output dataset

### IF YOU WANT TO WRITE NUMPY ARRAY TO DISK, (num_grains x GRAIN_LEN)
np.save(os.path.join(OUTPUT_FOLDER, "sines.npy"), sines)

### IF YOU WANT TO WRITE WAV FILES TO DISK:
# [sf.write(os.path.join(OUTPUT_FOLDER, f"{i:0>5d}.wav"), w, SR, "PCM_32") for i, w in enumerate(sines)]