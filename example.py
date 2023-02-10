from onto_cgan.cGAN.onto_cgan_init import CGAN
import pandas as pd
from gensim.models import Word2Vec
import numpy as np
import torch

ex = 'test.csv'
word2vec_file= 'opa2vec.model'

tabular_data = pd.read_csv(ex) #"resources/example_tabular_data_UCIAdult.csv")

embedddings = Word2Vec.load(word2vec_file)

omim_embeddings = {}
for i in embedddings.wv.key_to_index.keys():
    if "http://mowl.borg/OMIM_" in i:
        omim_embeddings[i] = embedddings.wv[i]


data = omim_embeddings.items()
dataMatrix = np.array([omim_embeddings[i] for i in omim_embeddings])
omim_embeddings = torch.from_numpy(dataMatrix)
print(len(omim_embeddings))

# We adjusted the original CTGAN model from SDV. Instead of looking at the distribution of individual variable, we extended to two variables and keep their corrll

model = CGAN(
   epochs=10, ### number of training epochs
   batch_size=1000, ### the size of each batch
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
model.fit(tabular_data, omim_embeddings)
model.save("generator.pkl")

print("we done")
### Generate 100 synthetic rows
syn_data = model.sample(omim_embeddings, 2)
syn_data.to_csv("syn_data_file.csv")
print("we done done")