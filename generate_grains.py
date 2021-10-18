#Generate Grains from an audio file

import os

import numpy as np
import librosa
import soundfile as sf
from config import AUDIO_FOLDER, OUTPUT_FOLDER, SILENCE_CUTOFF

# Note: works best on input audio files with uniformly spaced info
def is_not_silent(audio_file):
    return (audio_file.max() > SILENCE_CUTOFF)

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

# throwaway quiet grains
final_grains = []
for g in grains:
	if is_not_silent(g):
		final_grains.append(librosa.util.normalize(g))

print(f"{float(len(final_grains))/len(grains)} of grains are viable for the data set, {len(final_grains)} to be exact.")

# output dataset

### IF YOU WANT TO WRITE NUMPY ARRAY TO DISK, (num_grains x GRAIN_LEN)
# np.save(os.path.join(OUTPUT_FOLDER, "grains.npy"), final_grains)

### IF YOU WANT TO WRITE WAV FILES TO DISK:
[sf.write(os.path.join(OUTPUT_FOLDER, f"{i:0>5d}.wav"), w, SR, "PCM_32") for i, w in enumerate(final_grains)]

