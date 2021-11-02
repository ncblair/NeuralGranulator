# Reference: https://python-osc.readthedocs.io/en/latest/server.html#threading-server
import numpy as np
import asyncio

from pythonosc import dispatcher
from pythonosc import osc_server

from config import IP, PORT, PARAMS

#IP = "192.168.1.207" # eudoram"169.231.37.250"
IP = "127.0.0.1"
PORT = 57121

LATENT_2D_ADDR = "/1/latent_xy"
ATTACK_ADDR = "/1/attack"
DECAY_ADDR = "/1/decay"
SUSTAIN_ADDR = "/1/sustain"
RELEASE_ADDR = "/1/release"

class OSCLatent:
	def __init__(self):
		self.latent_2d = np.zeros(2)
		self.attack = PARAMS["attack"]["start_val"]
		self.old_attack = PARAMS["attack"]["start_val"]
		self.decay = PARAMS["decay"]["start_val"]
		self.old_decay = PARAMS["decay"]["start_val"]
		self.sustain = PARAMS["sustain"]["start_val"]
		self.old_sustain = PARAMS["sustain"]["start_val"]
		self.release = PARAMS["release"]["start_val"]
		self.old_release = PARAMS["release"]["start_val"]

	def get_coordinates_handler(self,*args):
		address = args[0]
		# [-1, 1] -> [0,1]
		self.latent_2d = (np.array(args[1:]) + 1) * 0.5
		print(self.latent_2d)

	def need_adsr_update(self):
		return 	(self.attack != self.old_attack) or \
				(self.decay != self.old_decay) or \
				(self.sustain != self.old_sustain) or \
				(self.release != self.old_release)

	
	# Assumes that the recieved values are between 0 and 1.
	def attack_handler(self,*args):
		self.old_attack = self.attack
		address = args[0]
		min_val = PARAMS["attack"]["min_val"]
		max_val = PARAMS["attack"]["max_val"]
		self.attack = args[1] * (max_val-min_val) + min_val # do we need to make this atomic?
	
	def decay_handler(self,*args):
		self.old_decay = self.decay
		address = args[0]
		min_val = PARAMS["decay"]["min_val"]
		max_val = PARAMS["decay"]["max_val"]
		self.decay= args[1] * (max_val-min_val) + min_val
	
	def sustain_handler(self,*args):
		self.old_sustain = self.sustain
		address = args[0]
		min_val = PARAMS["sustain"]["min_val"]
		max_val = PARAMS["sustain"]["max_val"]
		self.sustain = args[1] * (max_val-min_val) + min_val
	
	def release_handler(self,*args):
		self.old_release = self.release
		address = args[0]
		min_val = PARAMS["release"]["min_val"]
		max_val = PARAMS["release"]["max_val"]
		self.release = args[1] * (max_val-min_val) + min_val

	def get_osc_coordinates(self):
		return self.latent_2d

handler = OSCLatent()
dispatcher = dispatcher.Dispatcher()
dispatcher.map(LATENT_2D_ADDR,handler.get_coordinates_handler)
dispatcher.map(ATTACK_ADDR,handler.attack_handler)
dispatcher.map(DECAY_ADDR,handler.decay_handler)
dispatcher.map(SUSTAIN_ADDR,handler.sustain_handler)
dispatcher.map(RELEASE_ADDR,handler.release_handler)



async def main_loop():
	while True:
		await asyncio.sleep(0)

if __name__ == "__main__":
	async def init_osc_latent():
		server = osc_server.AsyncIOOSCUDPServer(
				(IP, PORT), dispatcher,
				asyncio.get_event_loop())
		transport, protocol = await server.create_serve_endpoint()
		await main_loop()
		transport.close()
	asyncio.run(init_osc_latent())
