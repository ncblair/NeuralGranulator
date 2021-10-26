import numpy as np
import math

class ADSREnvelope:
	def __init__(self, attack_dur=1.0, decay_dur=0.2, sustain_level=0.7, \
				 release_dur=0.3, sample_rate=16000, frames_per_buffer=1024):
		self.attack_dur = attack_dur
		self.decay_dur = decay_dur
		self.sustain_level = sustain_level
		self.release_dur = release_dur
		self.sr = sample_rate
		self.is_trigger = False
		self.is_sustain = False
		self.is_release = False
		self.ads_index = 0
		self.r_index = 0
		self.frames_per_buffer = frames_per_buffer

		self.ads_data = np.concatenate((
						np.linspace(0,1, # attack data
							math.floor(self.attack_dur * self.sr)), 
						np.linspace(1, sustain_level, # decay data
							math.floor(self.decay_dur * self.sr))
		))

		self.r_data =  None # must be generate on the fly

		# Preallocate sustain data and zero data for SPEED
		self.s_data = np.array([sustain_level]*self.frames_per_buffer)
		self.zeros = np.zeros(frames_per_buffer)
	
	def set(self, attack_dur=0.05, decay_dur=0.2, sustain_level=0.7, \
				 release_dur=0.3):
		self.attack_dur = attack_dur
		self.decay_dur = decay_dur
		self.sustain_level = sustain_level
		self.release_dur = release_dur
		self.is_trigger = False
		self.is_sustain = False
		self.is_release = False
		self.ads_index = 0
		self.r_index = 0

		self.ads_data = np.concatenate((
					np.linspace(0,1, # attack data
						math.floor(self.attack_dur * self.sr)), 
					np.linspace(1, sustain_level, # decay data
						math.floor(self.decay_dur * self.sr))
		))

		self.r_data =  None # must be generated on the fly

		self.s_data = np.array([sustain_level]*self.frames_per_buffer)
	
	def trigger(self):
		self.ads_index = 0
		self.r_index = 0
		self.is_trigger = True
		self.is_release = False

	def release(self):
		self.is_release = True
		self.is_sustain = False
		self.r_data =  np.linspace(self.ads_data[self.ads_index], \
							0, math.floor(self.release_dur * self.sr))
	
	def is_done(self):
		return not self.is_trigger

	def get_audio_data(self, frame_count):
		if self.is_trigger and not self.is_release:
			return self.get_asd_data(frame_count)
		elif self.is_trigger and self.is_release:
			return self.get_r_data(frame_count)
		else:
			return self.zeros

	def get_asd_data(self, frame_count):
		if self.is_sustain:
			return self.s_data
		if self.ads_index + frame_count >= len(self.ads_data):
			self.is_sustain = True
			ad = self.ads_data[self.ads_index:]
			self.ads_index = len(self.ads_data) - 1
			return np.concatenate((ad,self.s_data[:frame_count-len(ad)]))

		data = self.ads_data[self.ads_index:self.ads_index + frame_count]
		self.ads_index += frame_count
		return data


	## MUST CALL RELEASE BEFORE CALLING THIS
	def get_r_data(self, frame_count):
		if not self.is_trigger or not self.is_release:
			return self.zeros

		if self.r_index + frame_count >= len(self.r_data):
			self.is_trigger = False
			self.is_release = False
			r = self.r_data[self.r_index:]
			self.r_index = len(self.r_data) - 1
			return np.concatenate((r,self.zeros[:frame_count - len(r)]))

		data = self.r_data[self.r_index:self.r_index + frame_count]
		self.r_index += frame_count
		return data