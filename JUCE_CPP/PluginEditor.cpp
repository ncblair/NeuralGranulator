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

    addDefaultKnob(&attack_knob, &attack_label);
    addDefaultKnob(&decay_knob, &decay_label);
    addDefaultKnob(&sustain_knob, &sustain_label);
    addDefaultKnob(&release_knob, &release_label);

    attack_knob.setBounds(1059, 512, 64, 76);
    decay_knob.setBounds(1214, 512, 64, 76);
    sustain_knob.setBounds(1059, 640, 64, 76);
    release_knob.setBounds(1214, 640, 64, 76);
    

    attack_label.setText("Attack", juce::dontSendNotification);
    decay_label.setText("Decay", juce::dontSendNotification);
    sustain_label.setText("Sustain", juce::dontSendNotification);
    release_label.setText("Release", juce::dontSendNotification);

    attack_knob.setValue(0.5);
    decay_knob.setValue(0.5);
    sustain_knob.setValue(0.5);
    release_knob.setValue(0.5);

    // model = torch::jit::load("D:\\PROJECTS\\2021_FALL\\013_JUCE_PROGRAM1\\PLUG_CMAKE_TORCH\\MODELS\\stft_model.pt");
    // background_image = juce::ImageFileFormat::loadFrom(juce::File("D:\\PROJECTS\\2021_FALL\\013_JUCE_PROGRAM1\\PLUG_CMAKE_TORCH\\IMG\\Layout.png"));

    // model = torch::jit::load("/Users/ncblair/COMPSCI/NeuralGranulator/JUCE_CPP/MODELS/stft_model.pt");
    background_image = juce::ImageFileFormat::loadFrom(juce::File("/Users/ncblair/COMPSCI/NeuralGranulator/JUCE_CPP/IMG/Layout.png"));

    std::cout << "ok\n";

}

AudioPluginAudioProcessorEditor::~AudioPluginAudioProcessorEditor()
{
}

void AudioPluginAudioProcessorEditor::addDefaultKnob(juce::Slider* slider, juce::Label* label) {
    slider->setSliderStyle(juce::Slider::SliderStyle::RotaryHorizontalVerticalDrag);
    slider->setRotaryParameters(-2.356f, 2.356f, 1);
    addAndMakeVisible(*slider);
    slider->setRange(0.0, 1.0);
    // slider->setTextValueSuffix (" ms");
    slider->setTextBoxStyle(juce::Slider::TextBoxBelow, true, 64, 12);
    slider->setColour(juce::Slider::ColourIds::textBoxTextColourId, juce::Colour(0, 0, 0));
    slider->setColour(juce::Slider::ColourIds::textBoxOutlineColourId, juce::Colour(255, 255, 255));
    slider->addListener(this);
    addAndMakeVisible(*label);
    label->attachToComponent(slider, false);
    label->setColour(juce::Label::ColourIds::textColourId, juce::Colour(0, 0, 0)); 
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

void AudioPluginAudioProcessorEditor::sliderValueChanged (juce::Slider* slider)
{
    processorRef.granulator.setADSR(attack_knob.getValue(), decay_knob.getValue(), sustain_knob.getValue(), release_knob.getValue());
    if (slider == &attack_knob){
        std::cout << "attack: " << slider->getValue() << std::endl;

    } 
    else if (slider == &decay_knob) {
        std::cout << "decay: " << slider->getValue() << std::endl;
    }
    else if (slider == &sustain_knob) {
        std::cout << "sustain: " << slider->getValue() << std::endl;
    }
    else if (slider == &release_knob) {
        std::cout << "release: " << slider->getValue() << std::endl;
    }
}