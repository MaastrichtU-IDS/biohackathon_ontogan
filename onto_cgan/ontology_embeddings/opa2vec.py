import mowl
mowl.init_jvm('10g')
from mowl.datasets import PathDataset
from mowl.corpus import extract_and_save_axiom_corpus
from mowl.owlapi import OWLAPIAdapter, OWLObjectPropertyAssertionAxiom
from mowl.reasoning import MOWLReasoner
from org.semanticweb.elk.owlapi import ElkReasonerFactory
from java.util import HashSet
from gensim.models.word2vec import LineSentence
from gensim.models import Word2Vec
import click as ck
import numpy as np
import pandas as pd
from sklearn.metrics import roc_curve, auc, matthews_corrcoef
from mowl.corpus import extract_and_save_axiom_corpus
from mowl.owlapi import OWLAPIAdapter
from mowl.reasoning import MOWLReasoner
from org.semanticweb.elk.owlapi import ElkReasonerFactory
from java.util import HashSet
import os

from mowl.corpus import extract_and_save_axiom_corpus, extract_and_save_annotation_corpus


@ck.command()
@ck.option('--dataset-folder', '-df', default='data/',
           help='A folder with dataset ontologies in owl format')
@ck.option(
    '--embed-dim', '-ed', default=128,
    help='Embedding dimension')
@ck.option(
    '--load', '-ld', is_flag=True, default=False, help='Load Model?')
    
def main(dataset_folder, embed_dim, load):
    dataset = PathDataset(
        f'{dataset_folder}/dataset.owl')
    if not load:
        reasoner_factory = ElkReasonerFactory()
        reasoner = reasoner_factory.createReasoner(dataset.ontology)
        mowl_reasoner = MOWLReasoner(reasoner)

        classes = dataset.ontology.getClassesInSignature()
        subclass_axioms = mowl_reasoner.infer_subclass_axioms(classes)
        equivalent_class_axioms = mowl_reasoner.infer_equivalent_class_axioms(classes)


        adapter = OWLAPIAdapter()
        manager = adapter.owl_manager
        
        axioms = HashSet()
        axioms.addAll(subclass_axioms)
        axioms.addAll(equivalent_class_axioms)
        
        manager.addAxioms(dataset.ontology, axioms)
        extract_and_save_axiom_corpus(dataset.ontology, f'{dataset_folder}/opa2vec_corpus.txt')
        extract_and_save_annotation_corpus(dataset.ontology, f'{dataset_folder}/opa2vec_corpus.txt', mode="a")

        sentences = LineSentence(f'{dataset_folder}/opa2vec_corpus.txt')
               
        model = Word2Vec(sentences, vector_size=embed_dim, epochs=10, window=5, min_count=1, workers=10)

        model.save(f'{dataset_folder}/opa2vec.model')
    else:
        model = Word2Vec.load(f'{dataset_folder}/opa2vec.model')

    
if __name__ == '__main__':
    main()
