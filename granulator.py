import pyaudio
import numpy as np
import librosa
import rtmidi.midiutil


# http://people.csail.mit.edu/hubert/pyaudio/docs/
# https://github.com/khalidtouch/XigmaLessons/blob/6d95e1961ce86a8258e398f00411b37ad5bc80bf/PYTHON/Music_Player_App/pygame/tests/midi_test.py
# https://stackoverflow.com/questions/31674416/python-realtime-audio-streaming-with-pyaudio-or-something-else

class OnMidiInput():
	def __init__(self, port, granulator):
		self.port = port
		self.gran = granulator
	def __call__(self, event, data=None):
		message, deltatime = event
		midi_type, midi_note, midi_velocity = message

		# TODO scale amplitude based on velocity
		# MIDI NOTE ON
		if midi_type == 144:
			self.gran.note_on(midi_note)
		# MIDI NOTE OFF
		if midi_type == 128:
			self.gran.note_off(midi_note)


class Granulator:

	def __init__(self):
		self.grains = {i:[0, [0], 0] for i in range(128)}
		self.counter = 0

	def __del__(self):
		self.close_audio_stream()
		self.close_midi_port()
	
	def replace_grain(self, grain):
		for note in self.grains:
			self.grains[note][2] = 0
		self.grains[60][1] = grain
		self.grains[60][2] = 1

	def init_audio_stream(self, sample_rate, bit_width, num_channels):
		self.sample_rate = sample_rate
		self.pya = pyaudio.PyAudio()
		self.stream = self.pya.open(format=self.pya.get_format_from_width(width=bit_width), channels=num_channels, rate=sample_rate, output=True, stream_callback=self.audio_callback)
	
	def init_midi(self):
		want_midi = input("Would you like to use MIDI? (y/N)")
		if want_midi != 'Y' and want_midi != 'y':
			self.midi_input = None
			self.grains[60][0] = 1
			return
		self.midi_input, self.port_name = rtmidi.midiutil.open_midiinput(-1)
		self.midi_input.set_callback(OnMidiInput(self.port_name,self))


	def start_audio_stream(self):
		self.stream.start_stream()

	# Put these in a destructor?
	def close_audio_stream(self):
		self.stream.stop_stream()
		self.stream.close()
		self.pya.terminate()

	def close_midi_port(self):
		if self.midi_input:
			self.midi_input.close_port()

	def note_on(self, note):
		self.grains[note][0] = 1
		if self.grains[note][2] == 0:
			self.grains[note][1] = librosa.effects.pitch_shift(self.grains[60][1], 
														self.sample_rate, 
														n_steps=note - 60)
			self.grains[note][2] = 1

	def note_off(self, note):
		self.grains[note][0] = 0
					
	
	def audio_callback(self, in_data, frame_count, time_info, status):
		# TODO TODO TODO, make this work pureley with array operations
		# num_repetitions = 1 + frame_count // self.grain_length
		# data = np.repeat(self.shiftedGrain, num_repetitions).astype(np.float32)
		# data = data[self.counter:self.counter + frame_count]
		data = np.zeros(frame_count, dtype="float32")

		grains = np.array([grain for note, (on, grain, _) in self.grains.items() if on])
		if grains.shape[0] > 0:
			grain = np.sum(grains, axis=0)
			count = 0
			for i in range(self.counter, self.counter + frame_count):
				data[count] = grain[i % len(grain)]
				count += 1

			self.counter = (self.counter + frame_count) % len(grain)
		

		return (data, pyaudio.paContinue)
