#pragma once

#include "PluginProcessor.h"

#include <torch/script.h>
#include <torch/torch.h>

#include <iostream>
#include <memory>
#include <thread>

#define GRAIN_SAMPLE_RATE (16000.0)

class XY_slider;

//==============================================================================
class AudioPluginAudioProcessorEditor  : public juce::AudioProcessorEditor, public juce::Slider::Listener
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

    // juce::Image background_image;

    int window_width;
    int window_height;
    // const int dev_w = 600;
    // const int dev_h = 400;
    bool grid_loaded = false;

    XY_slider* grid;
    juce::Slider attack_knob;
    juce::Slider decay_knob;
    juce::Slider sustain_knob;
    juce::Slider release_knob;
    juce::Slider grain_size_knob;
    juce::Slider mod_knob;
    juce::Label  attack_label;
    juce::Label  decay_label;
    juce::Label  sustain_label;
    juce::Label  release_label;
    juce::Label  grain_size_label;
    juce::Label  mod_label;

    void addDefaultKnob(juce::Slider* slider, juce::Label* label);
    void sliderValueChanged(juce::Slider* slider) override;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (AudioPluginAudioProcessorEditor)
};

class ML_thread : public juce::Thread {
    private: 
        torch::jit::script::Module model;
        const at::Tensor triangle_window = torch::cat( {torch::linspace(0.0f, 1.0f, GRAIN_SAMPLE_RATE/4), 
                                                        torch::linspace(1.0f, 0.0f, GRAIN_SAMPLE_RATE/4)});
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
            // auto time = juce::Time::getMillisecondCounter();
            auto mean = torch::zeros({1, 64});
            mean[0][0] = 6. * x - 3.;
            mean[0][1] = 6. * y - 3.;
            std::vector<torch::jit::IValue> inputs;
            inputs.push_back(torch::normal(0, .1, {1, 64}) + mean);

            c10::IValue result = model.forward(inputs);
            auto output = result.toTensor()[0];
            // output = triangle_window * output;
            // auto rolled = torch::roll(output, int(output.size(0)/2));
            // std::cout << rolled[rolled.size(0)/2] << " " << rolled[rolled.size(0)/2 - 1] << std::endl;
            // std::cout << rolled[0] << " " << rolled[rolled.size(0) - 1] << std::endl;
            // std::cout << output[0] << " " << output[output.size(0) - 1] << std::endl;
            // output = output + rolled;
            // std::cout << output[0] << " " << output[output.size(0) - 1] << std::endl;

            // std::cout << "Model Run Time: " << juce::Time::getMillisecondCounter() - time << std::endl;
            editor.processorRef.granulator.replace_grain(output);
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

class XY_slider: public juce::Component, public juce::Timer {
    public:
        float x_val;
        float y_val;
        std::atomic<bool> ready_to_update;
        ML_thread* background_thread;

        XY_slider(AudioPluginAudioProcessorEditor& e) : juce::Component{} {
            ready_to_update = true;
            background_thread = new ML_thread(e, "background_thread");
            background_thread->startThread(5);
            x_val = .5;
            y_val = .5;
            startTimer(33);
        }

        void mouseDrag(const juce::MouseEvent &event) override{
            gen_new_grain_if_ready(event);
        }

        void mouseDown(const juce::MouseEvent &event) override {
            gen_new_grain_if_ready(event);
        }
        void mouseUp(const juce::MouseEvent &event) override {
            gen_new_grain_if_ready(event);
        }
        
        void gen_new_grain_if_ready(const juce::MouseEvent& event) {
            auto x = get_normalized_x(event.getPosition().getX());
            auto y = get_normalized_y(event.getPosition().getY());
            auto x_normalized = (x * 2. - 1.)*(1. + 20. / getWidth());
            auto y_normalized = (y * 2. - 1.)*(1. + 20. / getHeight());
            auto distance_from_center = std::sqrt(x_normalized * x_normalized + y_normalized * y_normalized);
            if (distance_from_center > 1.0) {
                x_normalized = x_normalized / distance_from_center;
                y_normalized = y_normalized / distance_from_center;
            }
            x = (x_normalized/(1. + 20. / getWidth()) + 1.) / (2.);
            y = (y_normalized/(1. + 20. / getHeight()) + 1.) / (2.);
            x_val = x;
            y_val = y;
            background_thread->x = x_val;
            background_thread->y = y_val;
            background_thread->ready_to_update = true;
            repaint();

        }

        float get_normalized_x(int pixel_x) {
            return float(pixel_x) / float(getWidth());
        }

        float get_normalized_y(int pixel_y) {
            return float(pixel_y) / float(getHeight());
        }

        void timerCallback() override
        { 
            repaint();
        }

        void paint(juce::Graphics &g) override {
            //g.setColour (juce::Colours::yellow);
            g.setGradientFill(juce::ColourGradient(juce::Colour(100, 100, 155), 0.0f, 0.0f, juce::Colour(200, 200, 255), getWidth(), getHeight()/2., false));
            g.drawEllipse (1,1, getWidth() - 2, getHeight() - 2, 2);
            g.drawEllipse (x_val * getWidth() - 10, y_val * getHeight() - 10, 20, 20, 2);
            auto after_image = std::fmod((juce::Time::getMillisecondCounter() / 75.), 20.);
            g.setOpacity(1. - after_image/20.);
            g.drawEllipse (x_val * getWidth() - 10. - after_image / 2., 
                            y_val * getHeight() - 10. - after_image / 2., 
                            20 + after_image, 
                            20 + after_image, 
                            2);
        }
};