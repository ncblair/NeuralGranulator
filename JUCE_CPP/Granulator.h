#include <torch/script.h>
#include <torch/torch.h>
#include <juce_core/juce_core.h>
#include <juce_audio_utils/juce_audio_utils.h>
#include <juce_dsp/juce_dsp.h>

//=========GRANULATOR CLASSES
class Voice {
    private:
        int cur_sample;
        int cur_samp_offset;
        double grain_sr;
        int note_num_samples;
        juce::AudioSampleBuffer voice_playback_buffer; // to apply envelopes non-destructively
        juce::AudioSampleBuffer note_windowing_buffer; // to apply windowing non-destructively
        juce::AudioSampleBuffer note_buffer; // buffer for pitched notes
        // juce::AudioSampleBuffer next_note_buffer; //buffer for next note
        juce::AudioSampleBuffer grain_buffer; // buffer for model output in audio thread
        juce::AudioSampleBuffer temp_buffer; // buffer for model output in editor thread
        juce::Interpolators::Lagrange interp; //each voice gets its own resampling interpolator
        bool needs_update;
        bool needs_ramp;
    public:
        int note;
        float amp;
        bool key_pressed;
        bool making_noise;
        juce::ADSR* env; //each voice gets an adsr envelope pointer
        //juce::dsp::WindowingFunction<float> window;
        double percent_of_grain;
        double scan_percentage;

        // Constructor
        Voice();

        void update_grain();
        void queue_grain(const at::Tensor& grain);
        void note_on(int midinote, float amplitude=1.0);
        void note_off();
        void pitch_voice();
        void mix_in_voice(juce::AudioSampleBuffer& buffer, int total_samples);
        void tensor_to_buffer(const at::Tensor& tensor, juce::AudioSampleBuffer& buffer);
        void set_scan_percentage(double scan_percent);
        void set_percent_grain(double percent_grain);
        void smooth_grain();
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
        void set_grain_size(double percent_of_grain);
        void set_scan(double scan_percentage);
};