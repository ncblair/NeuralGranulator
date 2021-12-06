#include "PluginProcessor.h"
#include "PluginEditor.h"

#include <thread>

//==============================================================================
AudioPluginAudioProcessorEditor::AudioPluginAudioProcessorEditor (AudioPluginAudioProcessor& p)
    : AudioProcessorEditor (&p), processorRef (p)
{
    juce::ignoreUnused (processorRef);
    // Make sure that before the constructor has finished, you've set the
    // editor's size to whatever you need it to be.
    window_width = 1440;
    window_height = 899;
    setSize (window_width, window_height);

    grid = new XY_slider(*this);
    addAndMakeVisible(*grid);
    grid->setBounds(130, 252, 507, 507);

    // model = torch::jit::load("D:\\PROJECTS\\2021_FALL\\013_JUCE_PROGRAM1\\PLUG_CMAKE_TORCH\\MODELS\\stft_model.pt");
    // background_image = juce::ImageFileFormat::loadFrom(juce::File("D:\\PROJECTS\\2021_FALL\\013_JUCE_PROGRAM1\\PLUG_CMAKE_TORCH\\IMG\\Layout.png"));

    // model = torch::jit::load("/Users/ncblair/COMPSCI/NeuralGranulator/JUCE_CPP/MODELS/stft_model.pt");
    background_image = juce::ImageFileFormat::loadFrom(juce::File("/Users/ncblair/COMPSCI/NeuralGranulator/JUCE_CPP/IMG/Layout.png"));

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
    g.drawImage(background_image, 0, 0, window_width, window_height, 0, 0, dev_w, dev_h); // 1440 x 899 is background_image width
    //grid.paint(g);
}

void AudioPluginAudioProcessorEditor::resized()
{
    // This is generally where you'll want to lay out the positions of any
    // subcomponents in your editor..
}