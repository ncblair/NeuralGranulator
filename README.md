# NEURAL GRANULATOR

### Nathan Blair and Jack Kilgore

### CONTEXT:

Neural Granulator is a synthesizer that generates audio grains using a VAE neural network. Right now, the code is split between python and javascript, and soon will have a c++ implementation as well. Important code is in model.py, granulator.py, main.py, and config.py. GUI stuff has mostly been moved to the "INTERFACE" folder in javascript. 

### TODO MAT240A:

- get an example plugin compiled with PyTorch "Libtorch" and Juce and export to VST
- run c++ speed tests for the model

### TODO TRANSVERGENCE

- set up hand trackers
- finish web visualization
- Hook up all the knobs and start experimenting with different granulator knobs
- Train on larger Grains
- make temporally dynamic to differentiate from wavetable
- ml5.js option


### Completed MAT240A NOV 3:

- Converted pytorch model to Libtorch so it can be opened in c++ (Nathan)
- Ran example JUCE program and built as VST (didn't get joint config with pytorch yet) (Nathan)

### Completed Transvergence NOV 3:

- Added more OSC Hooks and got JS GUI working better (Jack)
- Added MIDI velocity (Jack)
