## Pipeline:

1. Generate concept embeddings from disease + function over Disease ontology + gene ontology + Human Phenotype Ontology
	1.1. Generate joint ontology files by joining them
	1.2. Add disease to OMIM mappings and gene functions
	1.3. Generate different embeddings for all using mOWL, but store embedding function mapping from axioms to embedding
2. Parse and pre-process MIMIC-III dataset
3. Build and train CGAN conditioned on axiom and concept embeddings based on MIMIC-III

