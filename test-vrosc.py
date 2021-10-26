# Reference: https://python-osc.readthedocs.io/en/latest/server.html#threading-server
import numpy as np
import asyncio

from pythonosc import dispatcher
from pythonosc import osc_server

IP = "192.168.1.207" # eudoram"169.231.37.250"
PORT = 57121

class OSCLatent :
	data = np.zeros(2)
	def get_coordinates_handler(self,*args):
		address = args[0]
		self.data = np.array(args[1:])
		print(self.data)

	def get_osc_coordinates(self):
		return self.data


osc_handler = OSCLatent()
dispatcher = dispatcher.Dispatcher()
dispatcher.map("/1/xy1",osc_handler.get_coordinates_handler)


async def main_loop():
	while True:
		# print(osc_handler.get_osc_coordinates())
		await asyncio.sleep(0)

async def init_osc_latent():
	server = osc_server.AsyncIOOSCUDPServer(
			(IP, PORT), dispatcher,
			asyncio.get_event_loop())
	transport, protocol = await server.create_serve_endpoint()
	await main_loop()
	transport.close()

asyncio.run(init_osc_latent())
