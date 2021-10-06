import pyaudio
import numpy as np
import librosa
import pygame.midi

# http://people.csail.mit.edu/hubert/pyaudio/docs/
# https://github.com/khalidtouch/XigmaLessons/blob/6d95e1961ce86a8258e398f00411b37ad5bc80bf/PYTHON/Music_Player_App/pygame/tests/midi_test.py
# https://stackoverflow.com/questions/31674416/python-realtime-audio-streaming-with-pyaudio-or-something-else


class Granulator:

	def __init__(self):
		self.grains = {i:[0, [0], 0] for i in range(128)}
		self.counter = 0
	
	def replace_grain(self, grain):
		for note in self.grains:
			self.grains[note][2] = 0
		self.grains[60][1] = grain
		self.grains[60][2] = 1

	def init_audio_stream(self, sample_rate, bit_width):
		self.sample_rate = sample_rate
		self.pya = pyaudio.PyAudio()
		self.stream = self.pya.open(format=self.pya.get_format_from_width(width=bit_width), channels=1, rate=sample_rate, output=True, stream_callback=self.callback)
	
	def init_midi(self):
		pygame.midi.init()
		in_id = pygame.midi.get_default_input_id()
		for indx in range(pygame.midi.get_count()):
			print(indx, pygame.midi.get_device_info(indx))
		in_id = int(input("input number of midi device or -1 for no midi"))
		if in_id != -1:
			self.midi_input = pygame.midi.Input(in_id)
			print(pygame.midi.get_device_info(in_id))
		else:
			self.midi_input = None
			self.grains[60][0] = 1


	def start_audio_stream(self):
		self.stream.start_stream()

	def close_audio_stream(self):
		self.stream.stop_stream()
		self.stream.close()
		self.pya.terminate()
		if self.midi_input:
			self.midi_input.close()
			pygame.midi.quit()

	def note_on(self, note):
		self.grains[note][0] = 1
		if self.grains[note][2] == 0:
			self.grains[note][1] = librosa.effects.pitch_shift(self.grains[60][1], 
														self.sample_rate, 
														n_steps=note - 60)
			self.grains[note][2] = 1

	def note_off(self, note):
		self.grains[note][0] = 0
					
	
	def callback(self, in_data, frame_count, time_info, status):
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
