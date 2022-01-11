# NEURAL GRANULATOR

### Nathan Blair and Jack Kilgore

### CONTEXT:

Neural Granulator is a synthesizer that generates audio grains using a VAE neural network. The JUCE VST code can be found in the JUCE_CPP folder. This repository also contains older python/javascript implementations and python code for training the neural network.

![Alt text](interface.png?raw=true "The Current Plug-In Interface")

### Installation / Reproducability (CPP, cmake):
 - Download JUCE and add it as a subdirectory of the JUCE_CPP folder
 - Download cmake (see: https://github.com/juce-framework/JUCE/blob/master/docs/CMake%20API.md)
 - Download Pytorch for c++ and cmake and add it as a subdirectory of the JUCE_CPP folder (Libtorch, see: https://pytorch.org/get-started/locally/, https://pytorch.org/cppdocs/installing.html) 
 - Download my torch model and put it in the JUCE_CPP/MODELS folder: https://drive.google.com/drive/folders/1hArulZDVrHTwexb-3Rt_8E9h5abi2d5d?usp=sharing (alternatively, generate a dataset and train a model in python)
 - Change the code in the PluginEditor.cpp constructor to match the paths on your filesystem.
 - Build the project 
```
mkdir build 
cd build 
cmake -DCMAKE_PREFIX_PATH=/absolute/path/to/libtorch ..
cmake --build .
```
 - The standalone application will be created in the build/JUCE_CPP_artefacts/Debug/Standalone directory
 - On macOS this code will also build a VST. The windows VST implementation is currently not working. 
 
### TODO JAN 11 2022:
- Collect new dataset(s) for grain generation. Guitar Loops, Plucked synth loops, Drum loops, and Spoken word/Soundtrack data are all of interest. 
- Train a new model – Change model architecture. Consult my AI-inclined friends on this and look through papers
- Look into asynchronous granulation and grain clouds implementation. Is that desirable for this instrument? A spray parameter + number of grains could be interesting. Is this computationally feasible?
- Fix segfaults by making program thread-safe

### Completed Dec 2021:
- implement envelopes, multiple voices, midi, pitching, knobs, control interface graphics
- Built custom UI features including 2D circular XY Slider
- Ran speed tests for model (5-10 ms to generate a grain)

### TODO MAT240A:

- implement envelopes, multiple voices, midi, pitching, stereo image, knobs, control interface graphics
- get an example plugin compiled with PyTorch "Libtorch" and Juce and export to VST
- run c++ speed tests for the model

### TODO TRANSVERGENCE

 - set up hand trackers
 - finish web visualization
 - Hook up all the knobs and start experimenting with different granulator knobs
 - Train on larger Grains
 - make temporally dynamic to differentiate from wavetable
 - ml5.js option
 
### Completed MAT240A NOV 31:
 - Implement custom X/Y slider graphics interface. 
 - Begin hooking up interface to audio generation
 - Running into a lot of issues with inheritance and passing information between contexts + generally has been a frustrating week working with JUCE. 

### Completed MAT240A NOV 24:
 - Implement resampling
 - Audio no longer glitches
 - Use JUCE buffer as back-end for granulator class operations in the audio thread
 - No allocation in audio thread
 - Mostly thread safe (besides one bool assignment)

### Completed MAT240A NOV 19:
 - Built simple granulator in JUCE using a libtorch backend (consider switching to c++/JUCE for performance)
 - Rebuilt pytorch model to bake in STFT (don't have to worry about it in c++ now)
 - Model loss now using time domain (something glitchy going on here too, examine lambda-VAE), probably convert back to freq domain
 - Able to generate random grains in JUCE using libtorch model and loop them. (sound quality is glitchy, something going wrong)

### Completed MAT240A NOV 12:
 - JUCE and Libtorch run together in standalone app. Print Libtorch Output in JUCE console

### Completed MAT240A NOV 3:

- Converted pytorch model to Libtorch so it can be opened in c++ (Nathan)
- Ran example JUCE program and built as VST (didn't get joint config with pytorch yet) (Nathan)

### Completed Transvergence NOV 3:

- Added more OSC Hooks and got JS GUI working better (Jack)
- Added MIDI velocity (Jack)

