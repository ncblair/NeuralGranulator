import os
import sys
import scandir
import copy
import random
import math

import numpy as np
import librosa
import soundfile as sf

from scipy import signal

PATH = os.getcwd()

AMOUNT_OF_FILES = 25000
MAX_NUM_FILES = 305979

WINDOW = True
SR = 16000 #khz
GRAIN_SEC = 0.1
GRAIN_LEN = int(GRAIN_SEC * SR) # sample
CHUNK_RANGE = 0.25  # RANGES FROM 0 to 1 where 1 means we chunk all of a sound file, 
                    # 0.5 is chunking half the sound file and so on
NP_OUT = True
SF_OUT = False

window = 1
if WINDOW:
	window = signal.tukey(GRAIN_LEN)

if len(sys.argv) != 3:
	print('Invalid number of arguments\nUsage: python filer_nsynth_set <nsynth-train folder to have filtered> <output folder>\n------------------')
	sys.exit(1)

if sys.argv[1].startswith("/") or sys.argv[1].startswith("~/") :
	INPUT_FOLDER = sys.argv[1]
else:
	INPUT_FOLDER = os.path.join(PATH,sys.argv[1])

if sys.argv[2].startswith("/") or sys.argv[2].startswith("~/") :
	OUTPUT_FOLDER = sys.argv[2]
else:
	OUTPUT_FOLDER = os.path.join(PATH, sys.argv[2])

if AMOUNT_OF_FILES > MAX_NUM_FILES:
    print(f"Must desire less than {MAX_NUM_FILES}.")
    sys.exit(1)

subset_percent = AMOUNT_OF_FILES / MAX_NUM_FILES


#Family 	Acoustic 	Electronic 	Synthetic 	Total
ACOUSTIC = 0
ELECTRONIC = 1
SYNTHETIC = 2
TOTAL = 3
instr_stats = {\
            'bass': [200,8387,60368,68955],\
            'brass' : [13760,70,0,13830],\
            'flute' : [6572,35,2816,9423],\
            'guitar' : [13343,16805,5275,35423],\
            'keyboard' : [8508,42645,3838,54991],\
            'mallet' : [27722,5581,1763,35066],\
            'organ' : [176,36401,0,36577],\
            'reed' : [14262,76,528,14866],\
            'string' : [20510,84,0,20594],\
            'synth_lead' : [0,0,5501,5501],\
            'vocal' : [3925,140,6688,10753],\
            'total' : [108978,110224,86777,305979]}

fam = {'acoustic': [], 'electronic': [], 'synthetic': []}
instr_names = {\
            'bass': copy.deepcopy(fam),
            'brass' : copy.deepcopy(fam),
            'flute' : copy.deepcopy(fam),
            'guitar' : copy.deepcopy(fam),
            'keyboard' : copy.deepcopy(fam),
            'mallet' : copy.deepcopy(fam),
            'organ' : copy.deepcopy(fam),
            'reed' : copy.deepcopy(fam),
            'string' : copy.deepcopy(fam),
            'synth_lead' : copy.deepcopy(fam),
            'vocal' : copy.deepcopy(fam)}

print("START GRABBING NAMES")
for root, dirs, files in scandir.walk(INPUT_FOLDER):
    # select file name
    for file in files:
        if file.endswith('.wav'):
            if not file.startswith('synth_lead'):
                f = file.split('_')[:2]
                instr_names[f[0]][f[1]].append(file)
            else:
                f = file.split('_')[:3]
                instr_names[f[0]+"_"+f[1]][f[2]].append(file)


# Get a subset of the files that is subset_percent, copy all those files

instr_names_subset = {\
            'bass': [],
            'brass' : [],
            'flute' : [],
            'guitar' : [],
            'keyboard' : [],
            'mallet' : [],
            'organ' : [],
            'reed' : [],
            'string' : [],
            'synth_lead' : [],
            'vocal' : []}

print("START SAMPLING")
for instrument in instr_names:
    count = 0
    for fams in instr_names[instrument]:
        if len(instr_names[instrument][fams]) < 1 :
            continue
        if len(instr_names[instrument][fams]) == 1 and instr_names[instrument][fams][0] == None:
            continue
        instr_names_subset[instrument] += random.sample(instr_names[instrument][fams],math.floor((subset_percent) * instr_stats[instrument][count]))
        count += 1

print("START CHUNKING")

for instrument in instr_names_subset:
    # import audio mono 16khz
    print(f"Start Loading in '{instrument}' Files...")
    if len(instr_names_subset[instrument]) < 1:
        continue

    wavs, rates = zip(*[librosa.load(os.path.join(INPUT_FOLDER, f), sr=SR) \
        for f in instr_names_subset[instrument]])
    print(f"End Loading in '{instrument}' Files...")

    print(f"Start Chunking '{instrument}' Files...")
    grains = []
    for w in wavs:
        w = np.concatenate((w, np.zeros((GRAIN_LEN - (w.shape[0] % GRAIN_LEN)))), axis=0) # zero padding
        grains += [g * window for g in np.split(w,w.shape[0]//GRAIN_LEN)[:math.floor((w.shape[0]//GRAIN_LEN)*CHUNK_RANGE)]]
    print(f"End Chunking '{instrument}' Files...")
    
    print(f"Start Outputting '{instrument}' Files...")

    if NP_OUT:
        np.save(os.path.join(OUTPUT_FOLDER, f"{instrument}-{int(GRAIN_SEC * 1000)}ms-grains.npy"), grains)
    
    if SF_OUT:
        sf_folder = os.path.join(OUTPUT_FOLDER,f"{instrument}-{int(GRAIN_SEC * 1000)}ms-grains")
        os.mkdir(os.path.join(sf_folder))
        [sf.write(os.path.join(sf_folder, f"{i:0>5d}.wav"), w, SR, "PCM_16") for i, w in enumerate(grains)]

    print(f"End Outputting '{instrument}' Files...")


        



