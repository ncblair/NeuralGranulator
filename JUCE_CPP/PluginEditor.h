#pragma once

#include "PluginProcessor.h"

#include <torch/script.h>
#include <torch/torch.h>

#include <iostream>
#include <memory>
#include <thread>

class XY_slider;

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

    AudioPluginAudioProcessor& processorRef;

private:
    // This reference is provided as a quick way for your editor to
    // access the processor object that created it.

    torch::jit::script::Module model;

    juce::TextButton new_grain_button;
    juce::Image background_image;

    int window_width;
    int window_height;
    const int dev_w = 1440;
    const int dev_h = 899;

    XY_slider* grid;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (AudioPluginAudioProcessorEditor)
};

class ML_thread : public juce::Thread {
    private: 
        torch::jit::script::Module model;
        AudioPluginAudioProcessorEditor& editor;
    public:
        std::atomic<int> x;
        std::atomic<int> y;
        std::atomic<int> w;
        std::atomic<int> h;
        std::atomic<bool> ready_to_update;
        ML_thread(AudioPluginAudioProcessorEditor& e, const juce::String &threadName) : editor(e), juce::Thread(threadName) {
            x = 0;
            y = 0;
            w = 1440;
            h = 899;
            model = torch::jit::load("/Users/ncblair/COMPSCI/NeuralGranulator/JUCE_CPP/MODELS/stft_model.pt");
            ready_to_update = true;
        }

        void gen_new_grain() {
            auto mean = torch::zeros({1, 64});
            mean[0][0] = 6 * x / w - 3;
            mean[0][1] = 6 * y / h - 3;
            std::vector<torch::jit::IValue> inputs;
            inputs.push_back(torch::normal(0, 1, {1, 64}) + mean);

            c10::IValue result = model.forward(inputs);
            auto output = result.toTensor();
            
            editor.processorRef.granulator.replace_grain(output[0]);
        }

        void run() {
            while (!threadShouldExit()) {
                if (ready_to_update) {
                    ready_to_update = false;
                    gen_new_grain();
                }
                else {
                    wait(-1);
                }
            }
        }

};

class XY_slider: public juce::Component {
    private:
        int x_val;
        int y_val;
    public:
        std::atomic<bool> ready_to_update;
        ML_thread* background_thread;

        XY_slider(AudioPluginAudioProcessorEditor& e) : juce::Component{} {
            ready_to_update = true;
            background_thread = new ML_thread(e, "background_thread");
            background_thread->startThread(0);
        }

        void mouseDrag(const juce::MouseEvent &event) override{
            gen_new_grain_if_ready(event);
        }

        void mouseDown(const juce::MouseEvent &event) override {
            gen_new_grain_if_ready(event);
        }
        
        void gen_new_grain_if_ready(const juce::MouseEvent& event) {
            x_val = event.getPosition().getX();
            y_val = event.getPosition().getY();
            background_thread->x = x_val;
            background_thread->y = y_val;
            background_thread->w = getWidth();
            background_thread->h = getHeight();
            background_thread->ready_to_update = true;
            repaint();
            background_thread->notify();
        }

        void paint(juce::Graphics &g) override {
            g.setColour (juce::Colours::yellow);
            g.drawEllipse (x_val, y_val, 20, 20, 3);
        }
};