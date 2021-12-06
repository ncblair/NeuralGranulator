#pragma once

#include "PluginProcessor.h"

#include <torch/script.h>
#include <torch/torch.h>

#include <iostream>
#include <memory>
#include <thread>

class XY_slider;

//==============================================================================
class AudioPluginAudioProcessorEditor  : public juce::AudioProcessorEditor
{
public:
    explicit AudioPluginAudioProcessorEditor (AudioPluginAudioProcessor&);
    ~AudioPluginAudioProcessorEditor() override;

    //==============================================================================
    void paint (juce::Graphics&) override;
    void resized() override;

    AudioPluginAudioProcessor& processorRef;

private:
    // This reference is provided as a quick way for your editor to
    // access the processor object that created it.

    torch::jit::script::Module model;

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
    public:
        AudioPluginAudioProcessorEditor& editor;
        std::atomic<float> x; // 0 to 1
        std::atomic<float> y; // 0 to 1
        std::atomic<bool> ready_to_update;
        ML_thread(AudioPluginAudioProcessorEditor& e, const juce::String &threadName) : juce::Thread(threadName), editor(e) {
            at::init_num_threads();
            model = torch::jit::load("/Users/ncblair/COMPSCI/NeuralGranulator/JUCE_CPP/MODELS/stft_model.pt");
            ready_to_update = true;
        }

        void gen_new_grain() {
            auto time = juce::Time::getMillisecondCounter();
            auto mean = torch::zeros({1, 64});
            mean[0][0] = 6. * x - 3.;
            mean[0][1] = 6. * y - 3.;
            std::vector<torch::jit::IValue> inputs;
            inputs.push_back(torch::normal(0, .1, {1, 64}) + mean);

            c10::IValue result = model.forward(inputs);
            auto output = result.toTensor();
            std::cout << "Model Run Time: " << juce::Time::getMillisecondCounter() - time << std::endl;
            
            editor.processorRef.granulator.replace_grain(output[0]);
        }

        void run() {
            std::cout << "ml thread started" << std::endl;
            while (!threadShouldExit()) {
                if (ready_to_update) {
                    ready_to_update = false;
                    gen_new_grain();
                }
            }
            std::cout << "exit ML thread" << std::endl;
        }

};

class XY_slider: public juce::Component {
    public:
        float x_val;
        float y_val;
        std::atomic<bool> ready_to_update;
        ML_thread* background_thread;

        XY_slider(AudioPluginAudioProcessorEditor& e) : juce::Component{} {
            ready_to_update = true;
            background_thread = new ML_thread(e, "background_thread");
            background_thread->startThread(5);
        }

        void mouseDrag(const juce::MouseEvent &event) override{
            gen_new_grain_if_ready(event);
        }

        void mouseDown(const juce::MouseEvent &event) override {
            gen_new_grain_if_ready(event);
        }
        
        void gen_new_grain_if_ready(const juce::MouseEvent& event) {
            x_val = get_normalized_x(event.getPosition().getX());
            y_val = get_normalized_y(event.getPosition().getY());
            background_thread->x = x_val;
            background_thread->y = y_val;
            // *background_thread->editor.processorRef.x_val = get_normalized_x(event.getPosition().getX());
            // *background_thread->editor.processorRef.y_val = get_normalized_y(event.getPosition().getY());
            background_thread->ready_to_update = true;
            repaint();
            //background_thread->notify();
        }

        float get_normalized_x(int pixel_x) {
            return float(pixel_x) / float(getWidth());
        }

        float get_normalized_y(int pixel_y) {
            return float(pixel_y) / float(getHeight());
        }

        void paint(juce::Graphics &g) override {
            g.setColour (juce::Colours::yellow);
            g.drawEllipse (int(x_val * getWidth()), int(y_val * getHeight()), 20, 20, 3);
        }
};