import mowl
mowl.init_jvm('10g')

from mowl.datasets import PathDataset
from mowl.corpus import extract_and_save_axiom_corpus
from mowl.owlapi import OWLAPIAdapter, OWLObjectPropertyAssertionAxiom
from mowl.reasoning import MOWLReasoner

from org.semanticweb.elk.owlapi import ElkReasonerFactory
from java.util import HashSet

from mowl.projection import OWL2VecStarProjector
from mowl.walking import DeepWalk, Node2Vec

from gensim.models.word2vec import LineSentence
from gensim.models import Word2Vec

import os

import click as ck
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import roc_curve, auc, matthews_corrcoef

from EmbeddingModules import ELEmbeddings


@ck.command()
@ck.option('--dataset-folder', '-df', default='data/',
           help='A folder with dataset ontologies in owl format')
@ck.option(
    '--embed-dim', '-ed', default=128,
    help='Embedding dimension')
@ck.option(
    '--load', '-ld', is_flag=True, help='Load Model?')
def main(dataset_folder, embed_dim, load):
    generate_embeddings(dataset_folder, embed_dim, load)

def generate_embeddings(ontology_path, 
                        embedding_method='owl2vec', 
                        data_root="data/", 
                        embed_dim=128, 
                        load=False):

    model = None
    dataset = PathDataset(f'{dataset_folder}/dataset.owl')
    if embedding_method=='owl2vec':
        model = owl2vec_fit(dataset, embed_dim=embed_dim)
        # @TODO implement prediction based on single/batched axioms
    elif embedding_method == 'ELEm':
        model = ELEm_fit(dataset, embed_dim=embed_dim)
    else:
        raise ValueError("Invalid ontology embedding method selected.")


def owl2vec_fit(dataset, embed_dim=128):
    if not load:
        projector = OWL2VecStarProjector(bidirectional_taxonomy=True)
        edges = projector.project(dataset.ontology)
        walker = DeepWalk(20, # number of walks per node
                20, # walk length
                0.1, # restart probability
                workers=4) # number of threads

        walks = walker.walk(edges)
        sentences = LineSentence(walker.outfile)
        model = Word2Vec(sentences, vector_size=embed_dim, epochs=10, window=5, min_count=1, workers=4)

        model.save(f'{dataset_folder}/owl2vec.model')
    else:
        model = Word2Vec.load(f'{dataset_folder}/owl2vec.model')

    return model

def ELEm_fit(dataset, embed_dim=128):
    el_dataset = ELDataset(dataset.ontology,
                        class_index_dict = None, 
                        object_property_index_dict = None, 
                        extended = True)
    model = ELEmbeddings(dataset,
                         embed_dim=10,
                         margin=0.1,
                         reg_norm=1,
                         learning_rate=0.001,
                         epochs=20,
                         batch_size=4096,
                         model_filepath=None,
                         device='cpu')
    model.train()
    return model


def owl2vec_predict(axioms):
    raise NotImplementedError


def generate_axioms():
    pass


if __name__ == '__main__':
    main()
   

