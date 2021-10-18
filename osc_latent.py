# Reference: https://python-osc.readthedocs.io/en/latest/server.html#threading-server
import numpy as np

from pythonosc import dispatcher
from pythonosc import osc_server

from config import IP, PORT

IP = "192.168.1.207" # eudoram"169.231.37.250"
PORT = 57121

class OSCLatent :
	data = np.zeros(2)
	def get_coordinates_handler(self,*args):
		address = args[0]
		self.data = np.array(args[1:])

	def get_osc_coordinates(self):
		return self.data

osc_handler = OSCLatent()
dispatcher = dispatcher.Dispatcher()
dispatcher.map("/1/xy1",osc_handler.get_coordinates_handler)

# dispatcher.map("/1/fader1",test)

