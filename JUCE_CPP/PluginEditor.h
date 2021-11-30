#pragma once

#include "PluginProcessor.h"
#include <torch/script.h>
#include <torch/torch.h>

#include <iostream>
#include <memory>

//==============================================================================
class AudioPluginAudioProcessorEditor  : public juce::AudioProcessorEditor, 
                                        public juce::Button::Listener
{
public:
    explicit AudioPluginAudioProcessorEditor (AudioPluginAudioProcessor&);
    ~AudioPluginAudioProcessorEditor() override;

    //==============================================================================
    void paint (juce::Graphics&) override;
    void resized() override;
    void buttonClicked (juce::Button* button) override;

private:
    // This reference is provided as a quick way for your editor to
    // access the processor object that created it.
    AudioPluginAudioProcessor& processorRef;

    torch::jit::script::Module model;

    juce::TextButton new_grain_button;
    juce::Image background_image;

    int window_width;
    int window_height;
    const int dev_w = 1440;
    const int dev_h = 899;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (AudioPluginAudioProcessorEditor)
};
