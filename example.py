from onto_cgan.cGAN.onto_cgan_init import CGAN
import pandas as pd
from gensim.models import Word2Vec
import numpy as np
import torch
import pickle as pkl


tabular_data_file = '../patient_measures.csv'
tabular_data = pd.read_csv(tabular_data_file) 


with open('../patients_embeddings.pkl', 'rb') as f:
    embeddings = pkl.load(f)

dataMatrix = np.array([embeddings[i] for i in embeddings])
embeddings = torch.from_numpy(dataMatrix)

print(embeddings.size)
print(tabular_data.shape)

# We adjusted the original CTGAN model from SDV. Instead of looking at the distribution of individual variable, we extended to two variables and keep their corrll

model = CGAN(
   epochs=10, ### number of training epochs
   batch_size=2000, ### the size of each batch
   log_frequency=True,
   verbose=True,
   generator_dim=(128, 128, 128),
   discriminator_dim=(128, 128, 128),
   generator_lr=2e-4, 
   discriminator_lr=2e-4,
   discriminator_steps=1, 
   private=False,
)
print("Start training model")
model.fit(tabular_data, embeddings)
model.save("generator_v2.pkl")

print("we done")
syn_data = model.sample(embeddings, 5)

syn_data.to_csv("syn_data_file_v2.csv")
print("we done done")