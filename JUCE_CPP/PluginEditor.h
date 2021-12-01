#pragma once

#include "PluginProcessor.h"
#include "xy_slider.cpp"

#include <torch/script.h>
#include <torch/torch.h>

#include <iostream>
#include <memory>


class XY_slider: public juce::Component {
    // private:
        
    public:
        int x_val;
        int y_val;
        //void mouseDown(const juce::MouseEvent &event) override;
        //void mouseDrag(const juce::MouseEvent &event) override;
        //void paint(juce::Graphics &g) override;
        XY_slider(int w, int h) : juce::Component{}{
            x_val = 0;
            y_val = 0;
        }
        XY_slider(XY_slider & source) : juce::Component{} {}
        XY_slider(XY_slider && source) : juce::Component{} {}

        void mouseDown(const juce::MouseEvent &event) override{
            x_val = event.getMouseDownX();
            y_val = event.getMouseDownY();
        }

        void mouseDrag(const juce::MouseEvent &event) override {
            x_val = event.getMouseDownX();
            y_val = event.getMouseDownY();
        }

        void paint(juce::Graphics &g) override {
            g.setColour (juce::Colours::yellow);
            g.drawEllipse (x_val, y_val, 20, 20, 3);
        }
};

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

    XY_slider grid = XY_slider{300, 300};

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (AudioPluginAudioProcessorEditor)
};

