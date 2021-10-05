import pyaudio
import numpy as np

# http://people.csail.mit.edu/hubert/pyaudio/docs/

# https://stackoverflow.com/questions/31674416/python-realtime-audio-streaming-with-pyaudio-or-something-else

class Granulator:

	def __init__(self):
		self.prevGrain = []
		self.currentGrain = []
		self.counter = 0
	
	def replace_grain(self, grain):
		self.prevGrain = self.currentGrain
		self.currentGrain = grain
	
	def init_audio_stream(self, sample_rate, bit_width):
		self.pya = pyaudio.PyAudio()
		self.stream = self.pya.open(format=self.pya.get_format_from_width(width=bit_width), channels=1, rate=sample_rate, output=True, stream_callback=self.callback)
	
	def start_audio_stream(self):
		self.stream.start_stream()

	def close_audio_stream(self):
		self.stream.stop_stream()
		stream.close()
		pya.terminate()
	
	def callback(self, in_data, frame_count, time_info, status):
		# TODO TODO TODO, make this work pureley with array operations
		data = np.zeros(frame_count, dtype="float32")
		count = 0
		for i in range(self.counter, self.counter + frame_count):
			data[count] = self.currentGrain[i % len(self.currentGrain)]
			count += 1

		self.counter = (self.counter + frame_count) % len(self.currentGrain)

		return (data, pyaudio.paContinue)


##### Testing stuff
import time

SR = 16000 #khz
GRAIN_LEN = 1600 # samples
FREQ = 220
BIT_WIDTH = 4
# generate sine array
samples = np.arange(GRAIN_LEN)
sine = np.sin(2 * np.pi * FREQ * samples / SR)

# initialize granulator
gran = Granulator()
gran.replace_grain(sine)

gran.init_audio_stream(SR, BIT_WIDTH)
gran.start_audio_stream()

while gran.stream.is_active():
   time.sleep(0.1)