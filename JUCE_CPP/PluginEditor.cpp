#include "PluginProcessor.h"
#include "PluginEditor.h"


//==============================================================================
AudioPluginAudioProcessorEditor::AudioPluginAudioProcessorEditor (AudioPluginAudioProcessor& p)
    : AudioProcessorEditor (&p), processorRef (p)
{
    juce::ignoreUnused (processorRef);
    // Make sure that before the constructor has finished, you've set the
    // editor's size to whatever you need it to be.
    addAndMakeVisible (new_grain_button);
    new_grain_button.setButtonText ("Gen New Grain");
    new_grain_button.addListener(this);
    setSize (400, 300);


    model = torch::jit::load("D:\\PROJECTS\\2021_FALL\\013_JUCE_PROGRAM1\\PLUG_CMAKE_TORCH\\MODELS\\stft_model.pt");

    std::cout << "ok\n";


}

AudioPluginAudioProcessorEditor::~AudioPluginAudioProcessorEditor()
{
}

//==============================================================================
void AudioPluginAudioProcessorEditor::paint (juce::Graphics& g)
{
    // (Our component is opaque, so we must completely fill the background with a solid colour)
    g.fillAll (getLookAndFeel().findColour (juce::ResizableWindow::backgroundColourId));

    g.setColour (juce::Colours::white);
    g.setFont (15.0f);
}

void AudioPluginAudioProcessorEditor::resized()
{
    // This is generally where you'll want to lay out the positions of any
    // subcomponents in your editor..
    new_grain_button.setBounds(10, 10, 100, 100);
}

void AudioPluginAudioProcessorEditor::buttonClicked (juce::Button* button)
{
    if (button == &new_grain_button)                                                      // [3]
        {
            auto mean = torch::zeros({1, 64});
            mean[0][0] = 3;
            std::vector<torch::jit::IValue> inputs;
            inputs.push_back(torch::normal(0, 1, {1, 64}) + mean);

            c10::IValue result = model.forward(inputs);
            auto output = result.toTensor();
            //std::cout<<output[0].size(0)<<std::endl;

            processorRef.granulator.replace_grain(output[0]);
        }
}