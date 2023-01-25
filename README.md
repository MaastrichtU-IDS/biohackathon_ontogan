# Onto-GAN - Biohackathon Mena 2023
This repository is a workplace for Team Onto-GAN in [Bio-Hackathon-Mena 2023](https://cbrcconferences.kaust.edu.sa/bio-hackathon-2023) in KAUST (7-11 Feb 2023). Planning, documentation, code, materials, and others related to the biohackathon will be shared here. The repo is private for now but will be public after consenting all team members and bio-hackathon organizers. 

### Team: 
[Chang Sun](https://www.linkedin.com/in/chang-sun-maastricht/), [Azza Altghafi](https://www.linkedin.com/in/azza-althagafi-b767aa144/), [Tilman Hinnerichs](https://tilman.hinnerichs.com/), [Maxat Kulmanov](https://www.linkedin.com/in/coolmaksat/?originalSubdomain=sa), [Núria Queralt Rosinach](https://www.linkedin.com/in/nqueralt/), [Michel Dumontier](https://www.linkedin.com/in/dumontier/). 

### Description 
The main objective of the proposed project is to generate realistic synthetic patients health data by embedding existing human knowledge (such as ontologies) into advanced deep generative model (Conditional Generative Adversarial Network models). We will integrate, for the first time, human knowledge (represented by ontologies), deep learning (Generative Adversarial Networks), Zero-Shot Learning, and privacy-preserving methods (Differential Privacy) in one generative framework. The primary use case we would like to apply in the Bio-hackathon is to generate synthetic health data for rara disease patient. Rare Diseases (incidence <1 in 2000) are life-threatening or chronically debilitating from early childhood and impose challenging social and economic burdens. The extreme heterogeneity and complexity of RDs and the sparsity of the available data cause difficulty in setting up research activities, delivering timely diagnosis and treatments (taking years and large costs to get correct diagnoses). Therefore, our motivation is to accelerate rare disease research and promote patients' well-being by generating more realistic patient data with both seen and unseen classes based on existing human knowledge and limited data.

To be more specific, beyond learning from data, we will embed rare disease ontological models from such as [Orphanet](https://www.orpha.net/consor/cgi-bin/index.php) or other exiting rare disease ontologies from MENA as conditional vectors into the generative model (GANS). The generative model 1) generates data that is structurally and statistically similar to the real seen data (deep learning), 2) generates data belonging to unseen classes or relations which are not observed in the real data, but represented in the ontologies (ontology embeddings). Then, we will 3) predict new classes that were not observed during training using zero-shot learning model, 4) add differetial privacy in the generative model to protect individual’s identity and provide privacy measure. 

### Planning (updated on 19 Jan 2023)
This planning is based on the meeting we had on 17th Jan 2023. Meeting note is accessible by request [Google doc](https://docs.google.com/document/d/1EDkHX7t7UmHipdjI2nuPkMW-8eVA0h4qmQFLOfr5IuM/edit?usp=sharing). 
#### Drafted plan:
- 7th Feb (Hello world and make a plan)
  - Introduction of the team and the project topic
  - Refine this work plan for the upcoming days
  - Select and prepare materials (dataset, ontologies, synthetic data model (e.g., GAN framework), embedding methods)
  - Define tasks based on team members expertise
  
- 8th Feb 
  - Finalize main methodology (embedding method, GAN structure, evaluation strategy for synthetic data)
  - Start embedding selected ontologies 
  - Structure GAN framework to take embeddings as additional input (other generators are also interesting to tryout)
  - Start making evaluation strategy (metrics)
  
- 9th and 10th Feb
  - Experiment 1: Input one ontology embeddings to GAN framework (tune hyperparameters for GAN)
  - Evaluate the quality of synthetic data (from Exp_1) based on our evaluation strategy
  
- 10th Feb
  - Experiment 2: Input two (and three) ontology embeddings to GAN framework 
  - Evaluate the quality of synthetic data (from Exp_2)
  - Experiment 3: Input three ontology embeddings to GAN framework 
  - Evaluate the quality of synthetic data (from Exp_)
  
- 11th Feb (Celebrate achievement and look forward)
  - Finalize the experiments and summarize the results
  - Discuss the results, conclude the findings, and present the work to other groups
  - Wrap up and plan for the next step (collaboration and publications)

#### Expected outcome:
- **Synthetic data generator (model/tool)** → to augment clinical data, evaluated, and tool can be used by the community
- **Predictor (model)** using zero-shoot learning → to predict patients with disease that we do not have the data 
- **Evalation benchmark** → to evaluate synthetic data including fidelity, utility, privacy, and other important factors.
- **Characterize the dataset** → which diseases are covered, what phenotypes are covered, patient embedding/clustering. compare patient disease space with total disease space
- **Societal impact for MENA community** → potential applications
- **Scientific publications** 

### Materials and resources
#### Potential use case: Duchenne Muscular Dystrophy
- Monogenetic rare disease (DMD gene)
- Mainly affects children & male
- Life-threatening
- Neuro and muscular phenotypes
- LUMC data?

#### Available datasets
- http://pavs.phenomebrowser.net/
- http://pavs.phenomebrowser.net/variants?term=Muscular%20Dystrophy%20Muscular&type=Phenotype (15K patients whose diagnoses were confirmed by clinicians)

#### Available ontologies:
- [HPO Ontology](https://hpo.jax.org/app/)
- [GO Ontology](http://geneontology.org/)
- Disease ontologies
  - [MONDO](https://www.ebi.ac.uk/ols/ontologies/mondo)
  - [OMIM](https://www.omim.org/)
  - [ORDO](https://www.ebi.ac.uk/ols/ontologies/ordo)
  - (Note from Núria: MONDO used to include OMIM and Orphanet RD Ontology)
  
 #### Possible Code to use
- GAN Framework:
  - DP-CGANS: https://github.com/sunchang0124/dp_cgans

- Ontology embeddings:
  - MOWL: https://mowl.readthedocs.io/en/latest/ 
  - OWL2VEC star: https://github.com/KRR-Oxford/OWL2Vec-Star

- Zero-shot learning

### Refereces
DATGAN: INTEGRATING EXPERT KNOWLEDGE INTO DEEP
LEARNING FOR SYNTHETIC TABULAR DATA
- [DATGAN: Integrating Expert Knowledge Into Depp Learning For Synthetic Tabular Data](https://arxiv.org/pdf/2203.03489.pdf)
- [OntoZSL: Ontology-enhanced Zero-shot Learning](https://dl.acm.org/doi/10.1145/3442381.3450042)

  



