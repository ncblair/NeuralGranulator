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

# make output folder if it doesn't exist

if (not os.path.exists(OUTPUT_FOLDER)):
	os.makedirs(OUTPUT_FOLDER)

# import audio mono 16khz
wavs, rates = zip(*[librosa.load(os.path.join(AUDIO_FOLDER, f), sr=SR) \
	for f in os.listdir(AUDIO_FOLDER) if f.endswith(".wav")])

# split into chunks
grains = [np.reshape(w[:(w.shape[0]//GRAIN_LEN)*GRAIN_LEN], (w.shape[0]//GRAIN_LEN, GRAIN_LEN)) for w in wavs]
# add grains from different audio files to same list
grains = np.concatenate(grains, axis = 0)

# output dataset

### IF YOU WANT TO WRITE NUMPY ARRAY TO DISK, (num_grains x GRAIN_LEN)
# np.save(os.path.join(OUTPUT_FOLDER, "grains.npy"), grains)

### IF YOU WANT TO WRITE WAV FILES TO DISK:
[sf.write(os.path.join(OUTPUT_FOLDER, f"{i:0>5d}.wav"), w, SR, "PCM_32") for i, w in enumerate(grains)]