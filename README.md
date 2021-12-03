# NEURAL GRANULATOR

### Nathan Blair and Jack Kilgore

### CONTEXT:

Neural Granulator is a synthesizer that generates audio grains using a VAE neural network. Right now, the code is split between python and javascript, and soon will have a c++ implementation as well. Important code is in model.py, granulator.py, main.py, and config.py. GUI stuff has mostly been moved to the "INTERFACE" folder in javascript. 

### Installation / Reproducability (CPP, Windows, cmake):
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

