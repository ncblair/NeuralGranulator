# GOAL: Code a VAE in pytorch with waveNET style encoder/decoder

# REFERENCES:
"""
Pytorch VAE
- https://towardsdatascience.com/variational-autoencoder-demystified-with-pytorch-implementation-3a06bee395ed
Complicated tensorflow VAE WaveNET implementation
- https://github.com/magenta/magenta/blob/main/magenta/models/nsynth
Some basic nn code:
- https://pytorch.org/tutorials/beginner/blitz/neural_networks_tutorial.html
Small VAE Architecture for Audio:
- https://acids-ircam.github.io/variational-timbre/dafx18generative.pdf
Training VAE:
- https://backend.orbit.dtu.dk/ws/portalfiles/portal/121765928/1602.02282.pdf
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np


###
"""
audio --> wavenet encoder --> latent space --> wavenet decoder --> audio
"""
###

class GrainVAE(nn.Module):
	def __init__(self, grain_length, use_cuda=True):
		super(GrainVAE, self).__init__()

		self.grain_length = grain_length
		self.h_dim = 512 # hidden dimension
		self.l_dim = 64 # latent dimension
		self.hidden_layers = 2
		self.sr = 16000
		self.use_cuda = use_cuda

		# encoder layers
		self.fc1 = nn.Linear(self.grain_length, self.h_dim)
		self.hidden_encoders = []
		for i in range(self.hidden_layers):
			if self.use_cuda:
				self.hidden_encoders.append(nn.Linear(self.h_dim, self.h_dim).cuda())
			else:
				self.hidden_encoders.append(nn.Linear(self.h_dim, self.h_dim))

		# go from encoder output to latent space
		self.fc_mu = nn.Linear(self.h_dim, self.l_dim)
		self.fc_var = nn.Linear(self.h_dim, self.l_dim)

		# decoder layers
		self.fc2 = nn.Linear(self.l_dim, self.h_dim)
		# self.hidden_decoders = []
		# for i in range(self.hidden_layers):
		# 	if self.use_cuda:
		# 		self.hidden_decoders.append(nn.Linear(self.h_dim, self.h_dim).cuda())
		# 	else:
		# 		self.hidden_decoders.append(nn.Linear(self.h_dim, self.h_dim))
		self.hidden_decoders = torch.nn.Sequential(
								*sum([[nn.Linear(self.h_dim, self.h_dim), nn.ReLU()]
								for i in range(self.hidden_layers)], []))

		self.fc3 = nn.Linear(self.h_dim, self.grain_length)

		self.log_scale = nn.Parameter(torch.Tensor([0.0]))

	def train_step(self, x, beta, y=None, lmbda=1):
		"""
		x is an input grain batch, batch_size x grain_length
		beta is the regularizer from Beta-VAE
		y is label batch
		lmbda is lambda-hot vector term that represents how far apart
			different classes should be in the latent space
		"""

		# encode x to get mu and std
		mu, log_var = self.encoder(x)
		std = torch.exp(log_var/2)

		# sample z from normal
		q = torch.distributions.Normal(mu, std)
		z = q.rsample()

		# decode z to get reconstruction
		x_hat = self.decoder(z)

		# Get Reconstruction Loss
		reconstruction_loss = self.reconstruction_loss(x_hat, x)

		# Get KL Loss
		kl_loss = self.kl_divergence_loss(z, mu, std, y, lmbda)
		#print(reconstruction_loss.mean(), kl_loss.mean())
		elbo = (beta*kl_loss - reconstruction_loss).mean()

		return elbo, beta*kl_loss.mean(), -reconstruction_loss.mean()

	def encoder(self, x):
		x = F.relu(self.fc1(x))
		for i in range(self.hidden_layers):
			x = F.relu(self.hidden_encoders[i](x))
		mu, log_var = self.fc_mu(x), self.fc_var(x)
		return mu, log_var

	# def decoder(self, z):
	# 	z = F.relu(self.fc2(z))
	# 	for i in range(self.hidden_layers):
	# 		z = F.relu(self.hidden_decoders[i](z))
	# 	z = self.fc3(z)
	# 	return z

	def decoder(self, z):
		z = F.relu(self.fc2(z))
		z = self.hidden_decoders(z)
		z = self.fc3(z)
		return z

	def forward(self, z):
		# define forward as just the decoder for tracing into c++
		self.decoder(z)

	def reconstruction_loss(self, x_hat, x):
		scale = torch.exp(self.log_scale)
		dist = torch.distributions.Normal(x_hat, scale)

		# measure prob of seeing image under p(x|z)
		log_pxz = dist.log_prob(x)
		log_pxz = log_pxz.sum(dim=(1)) # sum across output channel
		return log_pxz

	def kl_divergence_loss(self, z, mu, std, y=None, lmbda=1):
		# --------------------------
		# Monte carlo KL divergence
		# --------------------------
		# 1. define the first two probabilities (in this case Normal for both)
		if y is None:
			p = torch.distributions.Normal(torch.zeros_like(mu), torch.ones_like(std))
		else:
			mean = F.one_hot(y, z.shape[1])
			mean = mean.float().cuda() * lmbda
			p = torch.distributions.Normal(mean, torch.ones_like(std))
		q = torch.distributions.Normal(mu, std)

		# 2. get the probabilities from the equation
		log_qzx = q.log_prob(z)
		log_pz = p.log_prob(z)

		# kl
		kl = (log_qzx - log_pz)
		kl = kl.sum(-1)
		return kl

	def to_complex_repr(self, decoder_out):
		# put output of decoder back into complex domain
		decoder_out = decoder_out.cpu().detach().numpy()
		complex_out = np.zeros((decoder_out.shape[0], decoder_out.shape[1]//2)).astype(np.cdouble)
		complex_out.real = decoder_out[:, :decoder_out.shape[1]//2]
		complex_out.imag = decoder_out[:, decoder_out.shape[1]//2:]
		return complex_out
