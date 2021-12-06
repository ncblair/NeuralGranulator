#include <torch/script.h>
#include <torch/torch.h>
#include <juce_core/juce_core.h>
#include <juce_audio_utils/juce_audio_utils.h>
#include <juce_dsp/juce_dsp.h>

//=========GRANULATOR CLASSES
class Voice {
    private:
        int cur_sample;
        double grain_sr;
        int note_num_samples;
        juce::AudioSampleBuffer note_buffer; // buffer for pitched notes
        juce::AudioSampleBuffer grain_buffer; // buffer for model output in audio thread
        juce::AudioSampleBuffer temp_buffer; // buffer for model output in editor thread
        juce::Interpolators::Lagrange interp; //each voice gets its own resampling interpolator
        //juce::dsp::WindowingFunction<float> window; // each voice gets a triangle window for windowing.
        bool needs_update;
    public:
        int note;
        float amp;
        bool key_pressed;
        bool making_noise;
        juce::ADSR* env; //each voice gets an adsr envelope pointer

        // Constructor
        Voice();

        void update_grain();
        void queue_grain(const at::Tensor& grain);
        void note_on(int midinote, float amplitude=1.0);
        void note_off();
        void pitch_voice();
        void mix_in_voice(juce::AudioSampleBuffer& buffer, int total_samples);
        void tensor_to_buffer(const at::Tensor& tensor, juce::AudioSampleBuffer& buffer);
};

class Granulator {
    private:
        std::array<Voice, 12> voices; // 12 = MAX VOICES
    public:
        double grain_sample_rate;

        Granulator();
        void replace_grain(const at::Tensor& grain);
        void audio_callback(juce::AudioSampleBuffer& buffer, int total_samples);
        void note_on(int midinote, float amplitude);
        void note_off(int midinote);
        void setADSR(double attack, double decay, double sustain, double release);
};