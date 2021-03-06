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
    window_width = 600;
    window_height = 400;
    setSize (window_width, window_height);

    grid = new XY_slider(*this);
    grid_loaded = true;
    addAndMakeVisible(*grid);
    
    //grid->setBounds(int(window_width/12.), int(window_width/12.), int(window_width * 5. / 6.), int(window_width * 5. / 6.));
    grid->setBounds(int(window_width/12.), int(window_width/12.), int(window_width / 2.), int(window_width / 2.));
    addDefaultKnob(&attack_knob, &attack_label);
    addDefaultKnob(&decay_knob, &decay_label);
    addDefaultKnob(&sustain_knob, &sustain_label);
    addDefaultKnob(&release_knob, &release_label);
    addDefaultKnob(&grain_size_knob, &grain_size_label);
    addDefaultKnob(&scan_knob, &scan_label);

    // attack_knob.setBounds(1059, 512, 64, 76);
    // decay_knob.setBounds(1214, 512, 64, 76);
    // sustain_knob.setBounds(1059, 640, 64, 76);
    // release_knob.setBounds(1214, 640, 64, 76);
    

    attack_label.setText("Attack", juce::dontSendNotification);
    decay_label.setText("Decay", juce::dontSendNotification);
    sustain_label.setText("Sustain", juce::dontSendNotification);
    release_label.setText("Release", juce::dontSendNotification);
    grain_size_label.setText("Grain Size", juce::dontSendNotification);
    scan_label.setText("Grain Scan", juce::dontSendNotification);

    attack_knob.setRange(0.001, 1.0);
    decay_knob.setRange(0.001, 1.0);
    sustain_knob.setRange(0.001, 1.0);
    release_knob.setRange(0.001, 1.0);
    grain_size_knob.setRange(0.001, 1.0);
    scan_knob.setRange(0.0, 1.0);

    attack_knob.setValue(0.05);
    decay_knob.setValue(0.3);
    sustain_knob.setValue(1.0);
    release_knob.setValue(1.0);
    grain_size_knob.setValue(1.0);
    scan_knob.setValue(0.0);

    // model = torch::jit::load("D:\\PROJECTS\\2021_FALL\\013_JUCE_PROGRAM1\\PLUG_CMAKE_TORCH\\MODELS\\stft_model.pt");
    // background_image = juce::ImageFileFormat::loadFrom(juce::File("D:\\PROJECTS\\2021_FALL\\013_JUCE_PROGRAM1\\PLUG_CMAKE_TORCH\\IMG\\Layout.png"));

    // model = torch::jit::load("/Users/ncblair/COMPSCI/NeuralGranulator/JUCE_CPP/MODELS/stft_model.pt");
    //background_image = juce::ImageFileFormat::loadFrom(juce::File("/Users/ncblair/COMPSCI/NeuralGranulator/JUCE_CPP/IMG/Layout.png"));

    std::cout << "ok\n";
}

AudioPluginAudioProcessorEditor::~AudioPluginAudioProcessorEditor()
{
}

void AudioPluginAudioProcessorEditor::addDefaultKnob(juce::Slider* slider, juce::Label* label) {
    slider->setSliderStyle(juce::Slider::SliderStyle::RotaryHorizontalVerticalDrag);
    slider->setRotaryParameters(-2.356f, 2.356f, 1);
    addAndMakeVisible(*slider);
    // slider->setTextValueSuffix (" ms");
    slider->setTextBoxStyle(juce::Slider::TextBoxBelow, true, 64, 12);
    slider->setColour(juce::Slider::ColourIds::textBoxTextColourId, juce::Colour(200, 200, 255));
    slider->setColour(juce::Slider::ColourIds::textBoxOutlineColourId, juce::Colour::fromRGBA(0, 0, 0, 0));
    // slider->setColour(juce::Slider::ColourIds::trackColourId, juce::Colour(255, 255, 255));
    // slider->setColour(juce::Slider::ColourIds::thumbColourId, juce::Colour(0, 0, 0));
    slider->addListener(this);
    addAndMakeVisible(*label);
    label->attachToComponent(slider, false);
    label->setColour(juce::Label::ColourIds::textColourId, juce::Colour(200, 200, 255)); 
    slider->setColour(juce::Slider::ColourIds::trackColourId, juce::Colour(0, 0, 0));
    slider->setLookAndFeel (&knob_look);
    slider->setSkewFactor(0.5);
    // label->setNumDecimalPlacesToDisplay(3);
}

//==============================================================================
void AudioPluginAudioProcessorEditor::paint (juce::Graphics& g)
{
    g.setGradientFill(juce::ColourGradient(juce::Colour(0, 0, 50), 150.0f, 200.0f, juce::Colour(15, 15, 75), 490.0f, 225.0f, false));
    g.fillAll();
    g.setFont (15.0f);
}

void AudioPluginAudioProcessorEditor::resized()
{
    // This is generally where you'll want to lay out the positions of any
    // subcomponents in your editor..
    auto w = getWidth();
    auto h = getHeight();
    if (grid_loaded) {
        grid->setBounds(int(w/12.), int(w/12.), int(w / 2.), int(w / 2.));
    }
    attack_knob.setBounds(int(7. * w / 10.), int(3*h / 16.), int(w/10.), int(7.*w/60.));
    decay_knob.setBounds(int(8. * w / 10.), int(3*h / 16.), int(w/10.), int(7.*w/60.));
    sustain_knob.setBounds(int(7. * w / 10.), int(7*h / 16.), int(w/10.), int(7.*w/60.));
    release_knob.setBounds(int(8. * w / 10.), int(7*h / 16.), int(w/10.), int(7.*w/60.));
    grain_size_knob.setBounds(int(7. * w / 10.), int(11.*h / 16.), int(w/10.), int(7.*w/60.));
    scan_knob.setBounds(int(8. * w / 10.), int(11.*h / 16.), int(w/10.), int(7.*w/60.));
    
}

void AudioPluginAudioProcessorEditor::sliderValueChanged (juce::Slider* slider)
{
    processorRef.granulator.setADSR(attack_knob.getValue(), decay_knob.getValue(), sustain_knob.getValue(), release_knob.getValue());
    if (slider == &grain_size_knob) {
        processorRef.granulator.set_grain_size(grain_size_knob.getValue());
    }
    if (slider == &scan_knob) {
        processorRef.granulator.set_scan(scan_knob.getValue());
    }
}