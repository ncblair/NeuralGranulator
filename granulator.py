import pyaudio
import time

# http://people.csail.mit.edu/hubert/pyaudio/docs/

# https://stackoverflow.com/questions/31674416/python-realtime-audio-streaming-with-pyaudio-or-something-else

class Granulator:

	def __init__(self, sample_rate):
		self.sampleRate = sample_rate
		self.prevGrain = []
		self.currentGrain = []
	
	def add_grain(self, grain):
		self.prevGrain = self.currentGrain
		self.currentGrain = grain
	
	def init_audio_stream(self):
		self.pya = pyaudio.PyAudio()
		self.stream = self.pya.open(format=self.pya.get_format_from_width(width=1), channels=1, rate=self.sampleRate, output=True, stream_callback=self.callback)
	
	def start_audio_stream(self):
		self.stream.start_stream()

	def close_audio_stream(self):
		self.stream.stop_stream()
		stream.close()
		pya.terminate()
	
	def callback(self, in_data, frame_count, time_info, status):
		# TODO TODO TODO, send out duplicates of grain till it fits in `frame_count`
		data = np.zeros(frame_count) # SAVE ur ears (self.currentGrain * 0.000)
		return (data, pyaudio.paContinue) # TODO: understand paContinue


##### Testing stuff
import numpy as np
import os
import soundfile as sf


SR = 16000 #khz
GRAIN_LEN = 1024 # samples
FREQ = 220
# generate sine array
samples = np.arange(GRAIN_LEN)
sine = np.sin(2 * np.pi * FREQ * samples / SR)

# initialize granulator

gran = Granulator(SR)
gran.add_grain(sine)
gran.init_audio_stream()
gran.start_audio_stream()

while gran.stream.is_active():
    time.sleep(0.1)

#sf.write(os.path.join("~/Desktop/", "0.wav"), sine, SR, "PCM_16")
