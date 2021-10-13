import pyaudio
import numpy as np
import librosa
import math
import rtmidi.midiutil
from collections import deque

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

MAX_GRAIN_HISTORY = 20
OVERLAP = 0.5
NUM_OVERLAPS = 3
class GrainHistory:
	def __init__(self):
		self.history = deque(maxlen=MAX_GRAIN_HISTORY)
		self.current_grain = np.zeros(4800)
		self.index_grain = 0

	def add_grain(self, grain):
		self.history.append(grain)

	# def get_grain_overlap(self, size):
	# 	buffer = []
	def get_grain(self, size):
		start_overlap = math.floor(len(self.current_grain) *(1 - OVERLAP))
		is_curr_grain_dead = False
		buffer = []
		if len(self.history) < 1: 
			self.history.append(self.current_grain)
		overlap_buffer_count = 0
		for i in range(size):
			if self.index_grain + i > len(self.current_grain) - 1:
				is_curr_grain_dead = True
				buffer.append(self.history[0][overlap_buffer_count])
				overlap_buffer_count += 1
			elif self.index_grain + i > start_overlap and self.index_grain + i < len(self.current_grain):
				buffer.append(self.current_grain[self.index_grain+i] + self.history[0][overlap_buffer_count])
				overlap_buffer_count += 1
			else:
				buffer.append(self.current_grain[self.index_grain + i])
		
		if is_curr_grain_dead:
			self.index_grain = overlap_buffer_count
			# Only append if buffer is non-zero
			if self.current_grain.any():
				self.history.append(self.current_grain)
			self.current_grain = self.history.popleft()
		else:
			self.index_grain += size

		return buffer
		


class Granulator:

	def __init__(self):
		# 0 if note off, 1 if note on
		# the actual grain
		# 0 not ready, need to apply pitch shift, 1 : ready for audio loop
		self.grains = {i:[0, GrainHistory(), 0] for i in range(128)}
		self.counter = 0

	def __del__(self):
		self.close_audio_stream()
		self.close_midi_port()
	
	def replace_grain(self, grain):
		for note in self.grains:
			self.grains[note][2] = 0
		self.grains[60][1].add_grain(grain)
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
			# TODO TODO, GRAIN HISTORY BREAKS THIS
			self.grains[note][1].add_grain(librosa.effects.pitch_shift(self.grains[60][1].current_grain, 
														self.sample_rate, 
														n_steps=note - 60))
			self.grains[note][2] = 1

	def note_off(self, note):
		self.grains[note][0] = 0
					
	
	def audio_callback(self, in_data, frame_count, time_info, status):
		# TODO TODO TODO, make this work pureley with array operations
		# num_repetitions = 1 + frame_count // self.grain_length
		# data = np.repeat(self.shiftedGrain, num_repetitions).astype(np.float32)
		# data = data[self.counter:self.counter + frame_count]
		data = np.zeros(frame_count, dtype="float32")

		grains = np.array([grain.get_grain(frame_count) for note, (on, grain, _) in self.grains.items() if on])
		if grains.shape[0] > 0:
			grain = np.sum(grains, axis=0)
			count = 0
			for i in range(self.counter, self.counter + frame_count):
				data[count] = grain[i % len(grain)]
				count += 1

			self.counter = (self.counter + frame_count) % len(grain)
		

		return (data, pyaudio.paContinue)


        # def add_grain(self, grain):
        #         # first element is the index counter of the grain
        #         self.history.append([0,grain])

        # #TODO, not working as expected. what are you even trying to do?
        # # BIG LOGIC ERROR, you need to do number of overlaps per grainm rather than per block
        # def get_grain_2(self, size):
        #         buffer = np.zeros(size)
        #         is_curr_grain_dead = False
        #         start_overlap = math.floor(len(self.current_grain) *(1 - OVERLAP))

        #         if NUM_OVERLAPS > len(self.history):
        #                 return buffer

        #         overlap_grains = []
        #         for i in range(NUM_OVERLAPS):
        #                 overlap_grains.append(self.history[i])

        #         offset = 0
        #         how_much = size - offset
        #         count = 0
        #         for grain in overlap_grains:
        #                 far = None
        #                 index_grain = grain[0]
        #                 if index_grain + how_much > len(grain[1]):
        #                         far = len(grain[1])
        #                 else:
        #                         far = index_grain + how_much
        #                 diff = len(buffer[offset:]) - len(grain[1][index_grain:far])
        #                 # print(len(buffer[offset:]), len(grain[1][index_grain:far]))
        #                 output = None
        #                 if diff > 0:
        #                         (np.concatenate(grain[1][index_grain:far],np.zeros(diff)))
        #                 else:
        #                         output = grain[1][index_grain:far]
        #                 buffer[offset:] += output

        #                 offset += math.floor(OVERLAP_INTERVALS * len(grain[1]))
        #                 how_much = size - offset
        #                 count += 1
        #                 grain[0] = far
        #                 if diff != len(grain[1]):
        #                         # equivalenetly, self.history.rotate(-1)
        #                         # print("here")
        #                         g = self.history.popleft()
        #                         g[0] = 0
        #                         self.history.append(g)

        #                 if how_much < 0:
        #                         break

        #         return buffer