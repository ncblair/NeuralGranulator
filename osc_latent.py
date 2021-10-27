# Reference: https://python-osc.readthedocs.io/en/latest/server.html#threading-server
import numpy as np
import asyncio

from pythonosc import dispatcher
from pythonosc import osc_server

from config import IP, PORT

#IP = "192.168.1.207" # eudoram"169.231.37.250"
IP = "127.0.0.1"
PORT = 57121

LATENT_2D_ADDR = "/1/latent_xy"
ATTACK_ADDR = "1/attack"
DECAY_ADDR = "1/decay"
SUSTAIN_ADDR = "1/sustain"
RELEASE_ADDR = "1/release"

class OSCLatent:
	def __init__(self):
		latent_2d = np.zeros(2)
		attack

	def get_coordinates_handler(self,*args):
		address = args[0]
		# [-1, 1] -> [0,1]
		self.latent2d = (np.array(args[1:]) + 1) * 0.5
	
	def get_attack_handler(self,*args):
		address = args[0]
		self.attack = args[1]

	def get_osc_coordinates(self):
		return self.latent_2d

osc_handler = OSCLatent()
dispatcher = dispatcher.Dispatcher()
dispatcher.map(LATENT_2D_ADDR,osc_handler.get_coordinates_handler)
dispatcher.map(ATTACK_ADDR,osc_handler.get_attack_handler)



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
