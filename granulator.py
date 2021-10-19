import pyaudio
import numpy as np
import librosa
import math
import rtmidi.midiutil
from collections import deque
from scipy.signal import tukey, triang

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
		self.grain = None
		self.index_grain = 0
		self.sample_rate = sample_rate

		# Hardcode envelope for now
		self.envelope = ADSREnvelope(1,0.2,0.7,0.3,self.sample_rate)
	
	def pitch_voice(self, note):
		self.grain = librosa.resample(self.grain, 
						self.sample_rate, 
						self.sample_rate / (2**((note-60)/12)), 
						res_type="kaiser_fast")
	
	# run this only on grains that are triggered
	def replace_grain(self, grain):
		if not self.trigger:
			return

		self.grain = grain
		self.index_grain = 0
		if self.note not 60:
			pitch_voice(note)

	def note_on(self, grain, note):
		self.note = note
		replace_grain(grain)
		# init envelope 
		self.trigger = True

	def note_release(self):
		# start release, when done, set trigger to false
	
	def get_audio_data(self, size):
		# audio buffer = grab the smoothed grain and multiply it by current enevelope ?????
		# increment envelope and grain index by size
		# return audio buffer

		
		


class Granulator:

	def __init__(self):
		# 0 if note off, 1 if note on
		# the actual grain
		# 0 not ready, need to apply pitch shift, 1 : ready for audio loop
		self.grains = {i:[0, np.array([0]), 0] for i in range(128)}
		self.counter = {i: 0 for i in range(128)}
		self.voices = {i: Voice(SR) for i in range(128)}
		

	def __del__(self):
		self.close_audio_stream()
		self.close_midi_port()
		
	def replace_grain(self, grain):
		self.grains[60][1] = grain
		for note in self.grains:
			self.grains[note][2] = 0
			if self.grains[note][0] == 1:
				# note on
				self.note_on(note)
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
			self.grains[note][1] = librosa.resample(self.grains[60][1], 
													self.sample_rate, 
													self.sample_rate / (2**((note-60)/12)), 
													res_type="kaiser_fast")
			self.grains[note][2] = 1

	def note_off(self, note):
		self.grains[note][0] = 0

	# Note: this method uses knowledge of all grains globally, so it will be tricky to implement with the voice system.
	def get_smoothed_current_grain(self):
		# get all the grains that are on
		note_grains = [(note, grain) for note, (on, grain, _) in self.grains.items() if on]

		# if there are grains on, get frame_count samples from the sum of those grains
		if len(note_grains) > 0:
			notes, grains = zip(*note_grains)
			# smooth grains by adding two windowed grains together
			grains = [triang(g.shape[0])*g for g in grains]
			grains = [g + np.roll(g, len(g)//2) for g in grains]
			note_grains = list(zip(notes, grains))
		return note_grains


					
	def audio_callback(self, in_data, frame_count, time_info, status):
		# If no grains, just return the zero signal
		data = np.zeros(frame_count, dtype="float32")

		grains = self.get_smoothed_current_grain() # returns a list of note, grain
		if len(grains) > 0:
			# sample grains at each pitch to fill frame_count
			idx = lambda i: np.arange(self.counter[i], self.counter[i] + frame_count)
			data = [np.take(grain, idx(note), mode="wrap") for note, grain in grains]

			# sum different pitches together
			data = np.sum(data, axis=0).astype(np.float32)

			# increment counter that says where to sample from
			for note, grain in grains:
				self.counter[note] = (self.counter[note] + frame_count) % len(grain)

		return (data, pyaudio.paContinue)