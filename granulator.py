import pyaudio
import numpy as np
import librosa
import math
import rtmidi.midiutil
from collections import deque
from scipy.signal import tukey, triang
from ADSREnvelope import ADSREnvelope

from config import MAX_GRAIN_HISTORY, OVERLAP, NUM_OVERLAPS, SR

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

class Voice:
	def __init__(self, sample_rate):
		self.note = 60
		self.trigger = False
		# Maybe we hold onto a couple of grains that it can be smoothed with? IDfK
		self.base_grain = None
		self.grain = None
		self.index_grain = 0
		self.sample_rate = sample_rate

		# Hardcode envelope for now
		self.env = ADSREnvelope(1.0,1.3,0.5,0.3,sample_rate)
	
	def pitch_voice(self, note):
		if note == 60:
			self.grain = self.base_grain
		else:
			self.grain = librosa.resample(self.base_grain, 
						self.sample_rate, 
						self.sample_rate / (2**((note-60)/12)), 
						res_type="kaiser_fast")
	
	# run this only on grains that are triggered
	def replace_grain(self, grain):
		self.base_grain = grain
		if self.trigger:
			self.pitch_voice(self.note)


	# ASSUMES GRAIN EXISTS
	def note_on(self, note):
		self.pitch_voice(note)
		self.index_grain = 0
		self.note = note
		self.env.trigger()
		# init envelope 
		self.trigger = True
	
	def get_smoothed_grain(self):
		# smooth grains by adding two windowed grains together
		grain = triang(self.grain.shape[0])*self.grain
		grain = self.grain + np.roll(self.grain, len(self.grain)//2)
		return grain


	def note_release(self):
		self.env.release()
		return
	
	def get_audio_data(self, frame_count):
		# audio buffer = grab the smoothed grain and multiply it by current enevelope ?????
		g = self.get_smoothed_grain()
		idx = np.arange(self.index_grain, self.index_grain + frame_count)
		data = np.take(g, idx, mode="wrap") 
		env_data = self.env.get_audio_data(frame_count)
		data *= env_data
		# increment envelope and grain index by size
		self.index_grain = (self.index_grain + frame_count) % len(g)

		if self.env.is_done():
			self.trigger = False

		# return audio buffer
		return data

class Granulator:

	def __init__(self):
		# 0 if note off, 1 if note on
		# the actual grain
		# 0 not ready, need to apply pitch shift, 1 : ready for audio loop
		self.MAX_VOICES = 12
		self.frames_per_buffer = None
		self.grains = {i:[0, np.array([0]), 0] for i in range(128)}
		self.counter = {i: 0 for i in range(128)}
		self.voices = []
		for i in range(self.MAX_VOICES):
			self.voices.append(Voice(SR))		

	def __del__(self):
		self.close_audio_stream()
		self.close_midi_port()
	
	def replace_grain(self, grain):
		for voice in self.voices:
			# if voice.trigger:
			voice.replace_grain(grain)


	def init_audio_stream(self, sample_rate, bit_width, num_channels):
		self.sample_rate = sample_rate
		self.pya = pyaudio.PyAudio()
		self.stream = self.pya.open(format=self.pya.get_format_from_width(width=bit_width), 
						channels=num_channels, 
						rate=sample_rate, 
						output=True, 
						stream_callback=self.audio_callback
					)
		self.frames_per_buffer = self.stream._frames_per_buffer
	
	def init_midi(self):
		want_midi = input("Would you like to use MIDI? (y/N)")
		if want_midi != 'Y' and want_midi != 'y':
			self.midi_input = None
			self.voices[0].note_on(60)
			# self.grains[60][0] = 1
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
		available_voices = [voice for voice in self.voices if not voice.trigger]
		if len(available_voices) < 1:
			print("OUT OF VOICES!")
			return
		available_voices[0].note_on(note)

	def note_off(self, note):
		note_on_voices = [voice for voice in self.voices if voice.trigger and voice.note == note]
		for voice in note_on_voices:
			voice.note_release()

					
	def audio_callback(self, in_data, frame_count, time_info, status):
		# If no grains, just return the zero signal
		data = np.zeros(frame_count, dtype="float32")

		active_voices = [voice.get_audio_data(frame_count) for voice in self.voices if voice.trigger]

		if len(active_voices) > 0:
			# sum different pitches together
			data = np.sum(active_voices, axis=0).astype(np.float32)

		return (data, pyaudio.paContinue)