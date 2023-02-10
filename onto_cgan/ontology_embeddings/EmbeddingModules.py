import mowl
mowl.init_jvm("10g")
from mowl.base_models.elmodel import EmbeddingELModel
from mowl.nn.elmodule import ELModule

import torch as th
from torch import nn
import numpy as np

from tqdm import trange


class ELEmModule(ELModule):
    def __init__(self, nb_ont_classes, nb_rels, embed_dim=50, margin=0.1):
        super().__init__()
        self.nb_ont_classes = nb_ont_classes
        self.nb_rels = nb_rels

        self.embed_dim = embed_dim

        # Embedding layer for classes centers.
        self.class_embed = nn.Embedding(self.nb_ont_classes, embed_dim)
        nn.init.uniform_(self.class_embed.weight, a=-1, b=1)
        weight_data = th.linalg.norm(self.class_embed.weight.data, axis=1).reshape(-1, 1)
        self.class_embed.weight.data /= weight_data

        # Embedding layer for classes radii.
        self.class_rad = nn.Embedding(self.nb_ont_classes, 1)
        nn.init.uniform_(self.class_rad.weight, a=-1, b=1)
        weight_data = th.linalg.norm(self.class_rad.weight.data, axis=1).reshape(-1, 1)
        self.class_rad.weight.data /= weight_data

        # Embedding layer for ontology object properties
        self.rel_embed = nn.Embedding(nb_rels, embed_dim)
        nn.init.uniform_(self.rel_embed.weight, a=-1, b=1)
        weight_data = th.linalg.norm(self.rel_embed.weight.data, axis=1).reshape(-1, 1)
        self.rel_embed.weight.data /= weight_data

        self.margin = margin

    # Regularization method to force n-ball to be inside unit ball
    def class_reg(self, x):
        res = th.abs(th.linalg.norm(x, axis=1) - 1)
        res = th.reshape(res, [-1, 1])
        return res

    # Loss function for normal form :math:`C \sqsubseteq D`
    def gci0_loss(self, data, neg=False):
        c = self.class_embed(data[:, 0])
        d = self.class_embed(data[:, 1])
        rc = th.abs(self.class_rad(data[:, 0]))
        rd = th.abs(self.class_rad(data[:, 1]))
        dist = th.linalg.norm(c - d, dim=1, keepdim=True) + rc - rd
        loss = th.relu(dist - self.margin)
        return loss + self.class_reg(c) + self.class_reg(d)

    # Loss function for normal form :math:`C \sqcap D \sqsubseteq E`
    def gci1_loss(self, data, neg=False):
        c = self.class_embed(data[:, 0])
        d = self.class_embed(data[:, 1])
        e = self.class_embed(data[:, 2])
        rc = th.abs(self.class_rad(data[:, 0]))
        rd = th.abs(self.class_rad(data[:, 1]))

        sr = rc + rd
        dst = th.linalg.norm(d - c, dim=1, keepdim=True)
        dst2 = th.linalg.norm(e - c, dim=1, keepdim=True)
        dst3 = th.linalg.norm(e - d, dim=1, keepdim=True)
        loss = th.relu(dst - sr - self.margin) + th.relu(dst2 - rc - self.margin)
        loss += th.relu(dst3 - rd - self.margin)

        return loss + self.class_reg(c) + self.class_reg(d) + self.class_reg(e)

    # Loss function for normal form :math:`C \sqcap D \sqsubseteq \bot`
    def gci1_bot_loss(self, data, neg=False):
        c = self.class_embed(data[:, 0])
        d = self.class_embed(data[:, 1])
        rc = self.class_rad(data[:, 0])
        rd = self.class_rad(data[:, 1])

        sr = rc + rd
        dst = th.reshape(th.linalg.norm(d - c, axis=1), [-1, 1])
        return th.relu(sr - dst + self.margin) + self.class_reg(c) + self.class_reg(d)

    # Loss function for normal form :math:`C \sqsubseteq \exists R. D`
    def gci2_loss(self, data, neg=False):

        if neg:
            return self.gci2_loss_neg(data)

        else:
            # C subSelf.ClassOf R some D
            c = self.class_embed(data[:, 0])
            rE = self.rel_embed(data[:, 1])
            d = self.class_embed(data[:, 2])

            rc = th.abs(self.class_rad(data[:, 0]))
            rd = th.abs(self.class_rad(data[:, 2]))

            dst = th.linalg.norm(c + rE - d, dim=1, keepdim=True)
            loss = th.relu(dst + rc - rd - self.margin)
            return loss + self.class_reg(c) + self.class_reg(d)

    # Loss function for normal form :math:`C \nsqsubseteq \exists R. D`
    def gci2_loss_neg(self, data):

        c = self.class_embed(data[:, 0])
        rE = self.rel_embed(data[:, 1])

        d = self.class_embed(data[:, 2])
        rc = th.abs(self.class_rad(data[:, 1]))
        rd = th.abs(self.class_rad(data[:, 2]))

        dst = th.linalg.norm(c + rE - d, dim=1, keepdim=True)
        loss = th.relu(rc + rd - dst + self.margin)
        return loss + self.class_reg(c) + self.class_reg(d)

    # Loss function for normal form :math:`\exists R. C \sqsubseteq D`
    def gci3_loss(self, data, neg=False):

        rE = self.rel_embed(data[:, 0])
        c = self.class_embed(data[:, 1])
        d = self.class_embed(data[:, 2])
        rc = th.abs(self.class_rad(data[:, 1]))
        rd = th.abs(self.class_rad(data[:, 2]))

        euc = th.linalg.norm(c - rE - d, dim=1, keepdim=True)
        loss = th.relu(euc - rc - rd - self.margin)
        return loss + self.class_reg(c) + self.class_reg(d)

class ELEmbeddings(EmbeddingELModel):

    def __init__(self,
                 dataset,
                 embed_dim=50,
                 margin=0,
                 reg_norm=1,
                 learning_rate=0.001,
                 epochs=1000,
                 batch_size=4096 * 8,
                 model_filepath=None,
                 device='cpu'
                 ):
        super().__init__(dataset, batch_size, extended=True, model_filepath=model_filepath)

        self.embed_dim = embed_dim
        self.margin = margin
        self.reg_norm = reg_norm
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.device = device
        self._loaded = False
        self._loaded_eval = False
        self.extended = False
        self.init_model()

    def init_model(self):
        self.model = ELEmModule(
            len(self.class_index_dict),  # number of ontology classes
            len(self.object_property_index_dict),  # number of ontology object properties
            embed_dim=self.embed_dim,
            margin=self.margin
        ).to(self.device)

    def train(self):
        optimizer = th.optim.Adam(self.model.parameters(), lr=self.learning_rate)
        best_loss = float('inf')

        for epoch in trange(self.epochs):
            self.model.train()

            train_loss = 0
            loss = 0

            # Notice how we use the ``training_datasets`` variable directly
            # and every element of it is a pair (GCI name, GCI tensor data).
            for gci_name, gci_dataset in self.training_datasets.items():
                if len(gci_dataset) == 0:
                    continue

                loss += th.mean(self.model(gci_dataset[:], gci_name))
                if gci_name == "gci2":
                    prots = [self.class_index_dict[p] for p in self.dataset.evaluation_classes.as_str]
                    idxs_for_negs = np.random.choice(prots, size=len(gci_dataset), replace=True)
                    rand_index = th.tensor(idxs_for_negs).to(self.device)
                    data = gci_dataset[:]
                    neg_data = th.cat([data[:, :2], rand_index.unsqueeze(1)], dim=1)
                    loss += th.mean(self.model(neg_data, gci_name, neg=True))

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            train_loss += loss.detach().item()

            loss = 0
            with th.no_grad():
                #@TODO How to evaluate?
                self.model.eval()
                valid_loss = 0
                gci2_data = self.validation_datasets["gci2"][:]
                loss = th.mean(self.model(gci2_data, "gci2"))
                valid_loss += loss.detach().item()

            checkpoint = 1
            if best_loss > valid_loss:
                best_loss = valid_loss
                th.save(self.model.state_dict(), self.model_filepath)
            if (epoch + 1) % checkpoint == 0:
                print(f'\nEpoch {epoch}: Train loss: {train_loss:4f} Valid loss: {valid_loss:.4f}')

    def predict_axiom_emb(self):
        #@TODO generate the embedding
        self.init_model()
        print('Load the best model', self.model_filepath)
        self.model.load_state_dict(th.load(self.model_filepath))
        with th.no_grad():
            self.model.eval()

            eval_method = self.model.gci2_loss

            evaluator = ELEmbeddingsPPIEvaluator(
                self.dataset.testing, eval_method, self.dataset.ontology,
                self.class_index_dict, self.object_property_index_dict, device=self.device)
            evaluator()
            evaluator.print_metrics()

    def evaluate_ppi(self):
        self.init_model()
        print('Load the best model', self.model_filepath)
        self.model.load_state_dict(th.load(self.model_filepath))
        with th.no_grad():
            self.model.eval()

            eval_method = self.model.gci2_loss

            evaluator = ELEmbeddingsPPIEvaluator(
                self.dataset.testing, eval_method, self.dataset.ontology,
                self.class_index_dict, self.object_property_index_dict, device=self.device)
            evaluator()
            evaluator.print_metrics()