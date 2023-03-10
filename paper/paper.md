---
title: 'BioHackrXiv  template'
tags:
  - CGAN
  - synthetic data
  - NeSy AI
  - GAN
authors:
  - name: Santa Clause
    orcid: 0000-0000-0000-0000
    affiliation: 1
  - name: Second Last
    orcid: 0000-0000-0000-0000
    affiliation: 2

affiliations:
 - name: Institution 1, address, city, country
   index: 1
 - name: Institution 1, address, city, country
   index: 2
date: 12 February 2022
bibliography: paper.bib
authors_short: Last et al. (2021) BioHackrXiv  template
group: BioHackrXiv
event: BioHackathon MENA 2023
---

# Introduction or Background

As the name suggests, "rare diseases" are fairly uncommon leading to limited availability of patient data for such diseases. Rare Diseases (incidence <1 in 2000) are life-threatening or chronically debilitating from early childhood and impose challenging social and economic burdens. The extreme heterogeneity and complexity of RDs and the sparsity of the available data cause difficulty in setting up research activities, delivering timely diagnosis and treatments (taking years and large costs to get correct diagnoses). Therefore, our motivation is to accelerate rare disease research and promote patients' well-being by generating more realistic patient data with both seen and unseen classes based on existing human knowledge and limited data.

Especially clinical measurement data is crucial and important for training of human and AI diagnosis training. Unfortunately, artificially generating patient data for such diseases or diseases without any given patient data is an unsolved issue for now with high relevance and impact. With this BioHackathon MENA 2023 project we approach to generate realistic synthetic patients health data by embedding existing human knowledge (such as ontologies) into advanced deep generative model (Conditional Generative Adversarial Network models). 

We approach this issue by semantically embedding diseases and collections of phenotypes for which artificial patient data shall be generated by exploiting ontologies using the mOWL library (CITATION). We then condition the GAN on this label embedding to generate patients. Due to semantically structuring the conditioning space of the GAN, we may formulate axioms describing other diseases in the same representation space. Thus we are able to perform zero-shot generation for unseen diseases and phenotype collections that can be described over respective axioms. 

# Methods

Our work and implementation consists of three compartments. First, there is a collection of methods for preprocessing and filtering the MIMIC-III dataset (CITATION). Second, we join the Human Phenotype Ontology (HPO) with disease-phenotype associations and jointly embed them using different representation learning methods from mOWL. Third, we use the conditional GAN for tabular data (CITATION) to take care of generating both categorical and continuous measurement data. 

## Data

- the Medical Information for intensive Care III (MIMIC-III) dataset is large, anonymized and publicly available collectionf of medical records, including various measurements and corresponding disease diagnoses in form of ICD-9 codes. 
- we collect a subset of types of measurements that we are (1) available for the majority of the patients, and (2) are reasonably descriptive of the underlying range of possible diseases in the MIMIC-III dataset and our considered set of phenotypes
- We use the Human Phenotype Ontology that describes the inter-phenotype relations to structure our conditioning space. We therefore map all ICD-9 codes given in the MIMIC-III dataset to OMIM (CITATION) and associate all with their respective set of phenotypes.

## Contributions

- built entire pipeline incorporating the three compartments mentioned in the methods section
- introduced an regression loss inspired by natbib:citet (CITATION) that forces the discriminator to take the underlying ontology embeddings into account.  
- first neuro-symbolic generative model that is able to perform zero-shot generation
- show importance of semantically structuring the conditioning space



## Tables, figures and so on

Please remember to introduce tables (see Table 1) before they appear on the document. We recommend to center tables, formulas and figure but not the corresponding captions. Feel free to modify the table style as it better suits to your data.

Table 1
| Header 1 | Header 2 |
| -------- | -------- |
| item 1 | item 2 |
| item 3 | item 4 |

Remember to introduce figures (see Figure 1) before they appear on the document. 

![BioHackrXiv logo](./biohackrxiv.png)
 
Figure 1. A figure corresponding to the logo of our BioHackrXiv preprint.

# Other main section on your manuscript level 1

Feel free to use numbered lists or bullet points as you need.
* Item 1
* Item 2

# Discussion and/or Conclusion

We recommend to include some discussion or conclusion about your work. Feel free to modify the section title as it fits better to your manuscript.

# Future work

- Evaluation metrics

- extend to more complicated axioms and axiom spaces
    - use ELEm for embedding generation
- investigate the impact of loss functions on the quality of the data
- as the approach is universally applicable, we may explore embedding methods of axioms beyond first-order logic such as temporal or modal logic to construct generative models for prescription or predict mortality

## Questions

- Evaluation:
    - What are the strengths and weaknesses of "relatedness" w.r.t. the ontology for the generation?
        - leave out and predicting an entire branch vs. predicting on some left out siblings
- How to deal with the patients with multiple disease? (affect embeddings) 
    - Maybe we can do it on an axiomatic level?

# Jupyter notebooks, GitHub repositories and data repositories

* Please add a list here
* Make sure you let us know which of these correspond to Jupyter notebooks. Although not supported yet, we plan to add features for them
* And remember, software and data need a license for them to be used by others, no license means no clear rules so nobody could legally use a non-licensed research object, whatever that object is

# Acknowledgements
We acknowledge the contributions and ideas of Michel Dumontier, Robert Hoehndorf.

# References


