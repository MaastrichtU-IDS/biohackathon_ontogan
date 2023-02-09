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
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import roc_curve, auc, matthews_corrcoef


@ck.command()
@ck.option('--dataset-folder', '-df', default='data/',
           help='A folder with dataset ontologies in owl format')
@ck.option(
    '--embed-dim', '-ed', default=128,
    help='Embedding dimension')
@ck.option(
    '--load', '-ld', is_flag=True, help='Load Model?')
def main(dataset_folder, embed_dim, load):
    dataset = PathDataset(
        f'{dataset_folder}/dataset.owl')
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

        
    
if __name__ == '__main__':
    main()
