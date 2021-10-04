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


###
"""
audio --> wavenet encoder --> latent space --> wavenet decoder --> audio
"""
###

class GrainVAE(nn.Module):
	def __init__(self, grain_length, dtype=torch.cuda.FloatTensor):
		super(GrainVAE, self).__init__()

		self.grain_length = grain_length
		self.h_dim = 2000 # hidden dimension
		self.l_dim = 64 # latent dimension
		self.hidden_layers = 3
		self.sr = 16000
		self.dtype = dtype

		# encoder layers
		self.fc1 = nn.Linear(self.grain_length, self.h_dim)
		self.hidden_encoders = []
		for i in range(self.hidden_layers):
			self.hidden_encoders.append(nn.Linear(self.h_dim, self.h_dim).cuda())

		# go from encoder output to latent space
		self.fc_mu = nn.Linear(self.h_dim, self.l_dim)
		self.fc_var = nn.Linear(self.h_dim, self.l_dim)

		# decoder layers
		self.fc2 = nn.Linear(self.l_dim, self.h_dim)
		self.hidden_decoders = []
		for i in range(self.hidden_layers):
			self.hidden_decoders.append(nn.Linear(self.h_dim, self.h_dim).cuda())
		self.fc3 = nn.Linear(self.h_dim, self.grain_length)

		self.log_scale = nn.Parameter(torch.Tensor([0.0]))

	def train_step(self, x):
		"""
		x is an input grain batch, batch_size x grain_length
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
		kl_loss = self.kl_divergence_loss(z, mu, std)
		elbo = (kl_loss - reconstruction_loss).mean()

		return elbo

	def encoder(self, x):
		x = F.relu(self.fc1(x))
		for i in range(self.hidden_layers):
			x = F.relu(self.hidden_encoders[i](x))
		mu, log_var = self.fc_mu(x), self.fc_var(x)
		return mu, log_var

	def decoder(self, z):
		z = F.relu(self.fc2(z))
		for i in range(self.hidden_layers):
			z = F.relu(self.hidden_decoders[i](z))
		z = self.fc3(z)
		return z

	def reconstruction_loss(self, x_hat, x):
		scale = torch.exp(self.log_scale)
		dist = torch.distributions.Normal(x_hat, scale)

		# measure prob of seeing image under p(x|z)
		log_pxz = dist.log_prob(x)
		return log_pxz.sum(dim=(1))

	def kl_divergence_loss(self, z, mu, std):
		# --------------------------
		# Monte carlo KL divergence
		# --------------------------
		# 1. define the first two probabilities (in this case Normal for both)
		p = torch.distributions.Normal(torch.zeros_like(mu), torch.ones_like(std))
		q = torch.distributions.Normal(mu, std)

		# 2. get the probabilities from the equation
		log_qzx = q.log_prob(z)
		log_pz = p.log_prob(z)

		# kl
		kl = (log_qzx - log_pz)
		kl = kl.sum(-1)
		return kl
