from onto_cgan import DP_CGAN
import pandas as pd
from gensim.models import Word2Vec

ex = 'test.csv'
word2vec_file= '../../../opa2vec.model'

tabular_data = pd.read_csv(ex) #"resources/example_tabular_data_UCIAdult.csv")

embedddings = Word2Vec.load(word2vec_file)
embedddings = embedddings.wv

# We adjusted the original CTGAN model from SDV. Instead of looking at the distribution of individual variable, we extended to two variables and keep their corrll
model = DP_CGAN(
   epochs=10, # number of training epochs
   batch_size=1000, # the size of each batch
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
model.fit(tabular_data, embedddings)
model.save("generator.pkl")

# Generate 100 synthetic rows
syn_data = model.sample(100)
syn_data.to_csv("syn_data_file.csv")
