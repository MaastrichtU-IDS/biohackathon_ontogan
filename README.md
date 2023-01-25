# Onto-GAN - Biohackathon Mena 2023
This repository is a workplace for Team Onto-GAN in [Bio-Hackathon-Mena 2023](https://cbrcconferences.kaust.edu.sa/bio-hackathon-2023) in KAUST (7-11 Feb 2023). Planning, documentation, code, materials, and others related to the biohackathon will be shared here. The repo is private for now but will be public after consenting all team members and bio-hackathon organizers. 

### Team: 
[Chang Sun](https://www.linkedin.com/in/chang-sun-maastricht/), [Azza Altghafi](https://www.linkedin.com/in/azza-althagafi-b767aa144/), [Tilman Hinnerichs](https://tilman.hinnerichs.com/), [Maxat Kulmanov](https://www.linkedin.com/in/coolmaksat/?originalSubdomain=sa), [Núria Queralt Rosinach](https://www.linkedin.com/in/nqueralt/), [Michel Dumontier](https://www.linkedin.com/in/dumontier/). 

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


  



