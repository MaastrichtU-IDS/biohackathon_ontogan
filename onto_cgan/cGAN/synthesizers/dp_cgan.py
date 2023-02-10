### 2021-11-16 ###
# pos_weight in BCEWithLogitsLoss model #
# sigma = 5 #
# delta = 2e-6 #

import warnings

import numpy as np
import pandas as pd
import torch
from packaging import version
from torch import optim
from torch.nn import BatchNorm1d, Dropout, LeakyReLU, Linear, Module, ReLU, Sequential, functional, BCEWithLogitsLoss, utils
import torch.nn as nn

from onto_cgan.cGAN.data_sampler import DataSampler
from onto_cgan.cGAN.data_transformer import DataTransformer
from onto_cgan.cGAN.synthesizers.base import BaseSynthesizer

import scipy.stats

from datetime import datetime
from contextlib import redirect_stdout
from onto_cgan.cGAN.rdp_accountant import compute_rdp, get_privacy_spent


class Discriminator(Module):

    def __init__(self, input_dim, discriminator_dim, regr_dim=0, pac=10):
        super(Discriminator, self).__init__()
        dim = input_dim * pac
        self.pac = pac
        self.pacdim = dim
        seq = []
        for item in list(discriminator_dim):
            seq += [Linear(dim, item), LeakyReLU(0.2), Dropout(0.5)]
            dim = item

        self.seq = Sequential(*seq)
        self.rf_lin = [Linear(dim, 1)]
        self.regr_dim = regr_dim
        if self.regr_dim !=0:
            self.regr_lin = [Linear(dim, self.regr_dim)]

    def calc_gradient_penalty(self, real_data, fake_data, device='cpu', pac=10, lambda_=10):
        alpha = torch.rand(real_data.size(0) // pac, 1, 1, device=device)
        alpha = alpha.repeat(1, pac, real_data.size(1))
        alpha = alpha.view(-1, real_data.size(1))

        interpolates = alpha * real_data + ((1 - alpha) * fake_data)

        disc_interpolates = self(interpolates)
        if isinstance(disc_interpolates, tuple):
            disc_interpolates = disc_interpolates[0]

        gradients = torch.autograd.grad(
            outputs=disc_interpolates, inputs=interpolates,
            grad_outputs=torch.ones(disc_interpolates.size(), device=device),
            create_graph=True, retain_graph=True, only_inputs=True
        )[0]

        gradient_penalty = ((
            gradients.view(-1, pac * real_data.size(1)).norm(2, dim=1) - 1
        ) ** 2).mean() * lambda_

        return gradient_penalty

    def forward(self, input):
        assert input.size()[0] % self.pac == 0
        x = self.seq(input.view(-1, self.pacdim))
        return self.rf_lin(x), self.regr_lin(x)


class Residual(Module):

    def __init__(self, i, o):
        super(Residual, self).__init__()
        self.fc = Linear(i, o)
        self.bn = BatchNorm1d(o)
        self.relu = ReLU()

    def forward(self, input):
        out = self.fc(input)
        out = self.bn(out)
        out = self.relu(out)
        return torch.cat([out, input], dim=1)


class Generator(Module):

    def __init__(self, embedding_dim, generator_dim, data_dim):
        super(Generator, self).__init__()
        dim = embedding_dim
        seq = []
        for item in list(generator_dim):
            seq += [Residual(dim, item)]
            dim += item
        seq.append(Linear(dim, data_dim))
        self.seq = Sequential(*seq)

    def forward(self, input):
        data = self.seq(input)
        return data



class DPCGANSynthesizer(BaseSynthesizer):
    """Conditional Table GAN Synthesizer.

    This is the core class of the CTGAN project, where the different components
    are orchestrated together.
    For more details about the process, please check the [Modeling Tabular data using
    Conditional GAN](https://arxiv.org/abs/1907.00503) paper.
    Args:
        embedding_dim (int):
            Size of the random sample passed to the Generator. Defaults to 128.
        generator_dim (tuple or list of ints):
            Size of the output samples for each one of the Residuals. A Residual Layer
            will be created for each one of the values provided. Defaults to (256, 256).
        discriminator_dim (tuple or list of ints):
            Size of the output samples for each one of the Discriminator Layers. A Linear Layer
            will be created for each one of the values provided. Defaults to (256, 256).
        generator_lr (float):
            Learning rate for the generator. Defaults to 2e-4.
        generator_decay (float):
            Generator weight decay for the Adam Optimizer. Defaults to 1e-6.
        discriminator_lr (float):
            Learning rate for the discriminator. Defaults to 2e-4.
        discriminator_decay (float):
            Discriminator weight decay for the Adam Optimizer. Defaults to 1e-6.
        batch_size (int):
            Number of data samples to process in each step.
        discriminator_steps (int):
            Number of discriminator updates to do for each generator update.
            From the WGAN paper: https://arxiv.org/abs/1701.07875. WGAN paper
            default is 5. Default used is 1 to match original CTGAN implementation.
        log_frequency (boolean):
            Whether to use log frequency of categorical levels in conditional
            sampling. Defaults to ``True``.
        verbose (boolean):
            Whether to have print statements for progress results. Defaults to ``False``.
        epochs (int):
            Number of training epochs. Defaults to 300.
        pac (int):
            Number of samples to group together when applying the discriminator.
            Defaults to 10.
        cuda (bool):
            Whether to attempt to use cuda for GPU computation.
            If this is False or CUDA is not available, CPU will be used.
            Defaults to ``True``.
    """

    def __init__(self, embedding_dim=128, generator_dim=(256, 256), discriminator_dim=(256, 256),
                 generator_lr=2e-4, generator_decay=1e-6, discriminator_lr=2e-4,
                 discriminator_decay=1e-6, batch_size=500, discriminator_steps=1,
                 log_frequency=True, verbose=False, epochs=300, pac=10, cuda=True, private=False, conditional_columns=None):

        assert batch_size % 2 == 0

        self._embedding_dim = embedding_dim
        self._generator_dim = generator_dim
        self._discriminator_dim = discriminator_dim

        self._generator_lr = generator_lr
        self._generator_decay = generator_decay
        self._discriminator_lr = discriminator_lr
        self._discriminator_decay = discriminator_decay

        self._batch_size = batch_size
        self._discriminator_steps = discriminator_steps
        self._log_frequency = log_frequency
        self._verbose = verbose
        self._epochs = epochs
        self.pac = pac

        self.private = private
        self.conditional_columns = conditional_columns

        if not cuda or not torch.cuda.is_available():
            device = 'cpu'
        elif isinstance(cuda, str):
            device = cuda
        else:
            device = 'cuda'

        self._device = torch.device(device)

        self._transformer = None
        self._data_sampler = None
        self._generator = None
        self._discriminator = None

    @staticmethod
    def _gumbel_softmax(logits, tau=1, hard=False, eps=1e-10, dim=-1):
        """Deals with the instability of the gumbel_softmax for older versions of torch.

        For more details about the issue:
        https://drive.google.com/file/d/1AA5wPfZ1kquaRtVruCd6BiYZGcDeNxyP/view?usp=sharing
        Args:
            logits:
                […, num_features] unnormalized log probabilities
            tau:
                non-negative scalar temperature
            hard:
                if True, the returned samples will be discretized as one-hot vectors,
                but will be differentiated as if it is the soft sample in autograd
            dim (int):
                a dimension along which softmax will be computed. Default: -1.
        Returns:
            Sampled tensor of same shape as logits from the Gumbel-Softmax distribution.
        """
        if version.parse(torch.__version__) < version.parse("1.2.0"):
            for i in range(10):
                transformed = functional.gumbel_softmax(logits, tau=tau, hard=hard,
                                                        eps=eps, dim=dim)
                if not torch.isnan(transformed).any():
                    return transformed
            raise ValueError("gumbel_softmax returning NaN.")

        return functional.gumbel_softmax(logits, tau=tau, hard=hard, eps=eps, dim=dim)

    def _apply_activate(self, data):
        """Apply proper activation function to the output of the generator."""
        data_t = []
        st = 0
        for column_info in self._transformer.output_info_list:
            for span_info in column_info:
                if span_info.activation_fn == 'tanh':
                    ed = st + span_info.dim
                    data_t.append(torch.tanh(data[:, st:ed]))
                    st = ed
                elif span_info.activation_fn == 'softmax':
                    ed = st + span_info.dim
                    transformed = self._gumbel_softmax(data[:, st:ed], tau=0.2)
                    data_t.append(transformed)
                    st = ed
                else:
                    assert 0

        return torch.cat(data_t, dim=1)

    # def _cond_loss(self, data, c, m):
    #     """Compute the cross entropy loss on the fixed discrete column."""
    #     loss = []
    #     st = 0
    #     st_c = 0
    #     for column_info in self._transformer.output_info_list:
    #         for span_info in column_info:
    #             if len(column_info) != 1 or span_info.activation_fn != "softmax":
    #                 # not discrete column
    #                 st += span_info.dim
    #             else:
    #                 ed = st + span_info.dim
    #                 ed_c = st_c + span_info.dim
    #                 tmp = functional.cross_entropy(
    #                     data[:, st:ed],
    #                     torch.argmax(c[:, st_c:ed_c], dim=1),
    #                     reduction='none'
    #                 )
    #                 loss.append(tmp)
    #                 st = ed
    #                 st_c = ed_c

    #     loss = torch.stack(loss, dim=1)
    #     # print((loss * m).sum() / data.size()[0])
    #     return (loss * m).sum() / data.size()[0]

    def _cond_loss_pair(self, data, c_pair, m_pair):
        
        # m_pair = m_pair.detach().numpy()
        output_info_all_columns = self._transformer.output_info_list
        loss = torch.zeros((len(data)*int((m_pair.size()[1]*(m_pair.size()[1]-1))/2),m_pair.size()[1]))
        st_primary = 0
        st_primary_c = 0
        cnt = 0
        cnt_primary=0
        for index_primary in range(0, len(output_info_all_columns)):
            column_info_primary = output_info_all_columns[index_primary]
            for span_info_primary in column_info_primary:
                if len(column_info_primary) != 1 or span_info_primary.activation_fn != "softmax":
                    # not discrete column
                    st_primary += span_info_primary.dim
                else:
        
                    ed_primary = st_primary + span_info_primary.dim
                    ed_primary_c = st_primary_c + span_info_primary.dim

                    cnt_secondary=cnt_primary+1
                    st_secondary = ed_primary
                    st_secondary_c = ed_primary_c
                    for index_secondary in range(index_primary+1, len(output_info_all_columns)):
                        column_info_secondary = output_info_all_columns[index_secondary]
                        for span_info_secondary in column_info_secondary:
                            if len(column_info_secondary) != 1 or span_info_secondary.activation_fn != "softmax":
                                # not discrete column
                                st_secondary += span_info_secondary.dim
                            else:

                                ed_secondary = st_secondary + span_info_secondary.dim
                                ed_secondary_c = st_secondary_c + span_info_secondary.dim
                                
                                real_data_labels = torch.cat([data[:,st_primary:ed_primary], data[:,st_secondary:ed_secondary]], dim=1)
                                class_counts = real_data_labels.sum(axis=0)

                                
                                # pos_weights = torch.ones_like(class_counts)
                                # neg_counts = [len(data)-pos_count for pos_count in class_counts]
                                # for cdx, (pos_count, neg_count) in enumerate(zip(class_counts,  neg_counts)):
                                #     pos_weights[cdx] = neg_count / (pos_count + 1e-5)
                                
                                # torch_pos_weights = torch.as_tensor(pos_weights, dtype=torch.float)
                                # print(pos_weights)

                                criterion = BCEWithLogitsLoss(reduction='none')#, pos_weight=pos_weights)
                                calculate_loss = criterion(
                                    torch.cat([data[:,st_primary:ed_primary], data[:,st_secondary:ed_secondary]], dim=1),
                                    torch.cat([c_pair[:,st_primary_c:ed_primary_c], c_pair[:,st_secondary_c:ed_secondary_c]],dim=1)
                                    )

                                # calculate_loss = calculate_loss.detach().numpy()
                                loss[cnt*len(data):(cnt+1)*len(data),cnt_primary] = calculate_loss[:,:span_info_primary.dim].sum(axis=1) * m_pair[:,cnt_primary]
                                loss[cnt*len(data):(cnt+1)*len(data),cnt_secondary] = calculate_loss[:,span_info_primary.dim:].sum(axis=1) * m_pair[:,cnt_secondary]

                                st_secondary = ed_secondary
                                st_secondary_c = ed_secondary_c
                                cnt += 1
                                cnt_secondary += 1

                    cnt_primary += 1
                    st_primary = ed_primary
                    st_primary_c = ed_primary_c
        # print(len(loss))
        return loss.sum() / len(loss)


    def _validate_discrete_columns(self, train_data, discrete_columns):
        """Check whether ``discrete_columns`` exists in ``train_data``.

        Args:
            train_data (numpy.ndarray or pandas.DataFrame):
                Training Data. It must be a 2-dimensional numpy array or a pandas.DataFrame.
            discrete_columns (list-like):
                List of discrete columns to be used to generate the Conditional
                Vector. If ``train_data`` is a Numpy array, this list should
                contain the integer indices of the columns. Otherwise, if it is
                a ``pandas.DataFrame``, this list should contain the column names.
        """
        if isinstance(train_data, pd.DataFrame):
            invalid_columns = set(discrete_columns) - set(train_data.columns)
        elif isinstance(train_data, np.ndarray):
            invalid_columns = []
            for column in discrete_columns:
                if column < 0 or column >= train_data.shape[1]:
                    invalid_columns.append(column)
        else:
            raise TypeError('``train_data`` should be either pd.DataFrame or np.array.')

        if invalid_columns:
            raise ValueError('Invalid columns found: {}'.format(invalid_columns))


    def fit(self, train_data, label_emb, discrete_columns=tuple(), loss_alpha=0.5 epochs=None):
        """Fit the CTGAN Synthesizer models to the training data.

        Args:
            train_data (torch.Tensor):
                Training Data. It must be a 2-dimensional torch.Tensor
            discrete_columns (list-like):
                List of discrete columns to be used to generate the Conditional
                Vector. If ``train_data`` is a Numpy array, this list should
                contain the integer indices of the columns. Otherwise, if it is
                a ``pandas.DataFrame``, this list should contain the column names.

                @TODO implement the above disambiguation for torch.Tensor
        """

        self._validate_discrete_columns(train_data, discrete_columns)

        if epochs is None:
            epochs = self._epochs
        else:
            warnings.warn(
                ('`epochs` argument in `fit` method has been deprecated and will be removed '
                 'in a future version. Please pass `epochs` to the constructor instead'),
                DeprecationWarning
            )

        self._transformer = DataTransformer()
        self._transformer.fit(train_data, discrete_columns)

        train_data = self._transformer.transform(train_data)

        self._data_sampler = DataSampler(
            train_data,
            self._transformer.output_info_list,
            self._log_frequency)

        data_dim = self._transformer.output_dimensions

        self._generator = Generator(
            self._embedding_dim + self._data_sampler.dim_cond_vec() + label_emb.size(1), # number of categories in the whole dataset + conditional vectors
            self._generator_dim,
            data_dim
        ).to(self._device)

        self._discriminator = Discriminator(
            data_dim + self._data_sampler.dim_cond_vec(),
            self._discriminator_dim,
            regr_dim=label_emb.size(1), # set to 0 to omit regression 
            pac=self.pac
        ).to(self._device)

        optimizerG = optim.Adam(
            self._generator.parameters(), lr=self._generator_lr, 
            betas=(0.5, 0.9),
            weight_decay=self._generator_decay
        )

        optimizerD = optim.Adam(
            self._discriminator.parameters(), lr=self._discriminator_lr,
            betas=(0.5, 0.9), 
            weight_decay=self._discriminator_decay
        )

        mean = torch.zeros(self._batch_size, self._embedding_dim, device=self._device)
        std = mean + 1

        steps_per_epoch = max(len(train_data) // self._batch_size, 1)
        with open('loss_output_%s.txt'%str(epochs), 'w') as f:
            with redirect_stdout(f):
                for i in range(epochs):
                    for id_ in range(steps_per_epoch):

                        for n in range(self._discriminator_steps):
                            fakez = torch.normal(mean=mean, std=std)

                            # condvec = self._data_sampler.sample_condvec(self._batch_size)
                            
                            condvec_pair = self._data_sampler.sample_condvec_pair(self._batch_size)
                            c_pair_1, m_pair_1, col_pair_1, opt_pair_1 = condvec_pair

                            if condvec_pair is None:
                                c_pair_1, m_pair_1, col_pair_1, opt_pair_1 = None, None, None, None
                                real = self._data_sampler.sample_data_pair(self._batch_size, col_pair_1, opt_pair_1)
                            else:
                                c_pair_1, m_pair_1, col_pair_1, opt_pair_1 = condvec_pair
                                c_pair_1 = torch.from_numpy(c_pair_1).to(self._device)
                                m_pair_1 = torch.from_numpy(m_pair_1).to(self._device)
                                fakez = torch.cat([fakez, c_pair_1], dim=1)

                                perm = np.arange(self._batch_size)
                                np.random.shuffle(perm)
            
                                real = self._data_sampler.sample_data_pair(self._batch_size, col_pair_1[perm], opt_pair_1[perm])
                                c_pair_2 = c_pair_1[perm]

                            sampled_label_emb = label_emb[torch.randint(0, label_emb.size(0), (self._batch_size,))]
                            fakez = torch.cat([fakez, sampled_label_emb], dim=1)  # Append vectors to be conditioned on label embeddings

                            fake = self._generator(fakez) # categories (unique value count) + continuous (1+n_components)
                            fakeact = self._apply_activate(fake)

                            real = torch.from_numpy(real.astype('float32')).to(self._device)
                            
                            # if c1 is not None:
                                # fake_cat = torch.cat([fakeact, c1], dim=1)
                                # real_cat = torch.cat([real, c2], dim=1)
                            if col_pair_1 is not None:
                                fake_cat = torch.cat([fakeact, c_pair_1], dim=1)
                                real_cat = torch.cat([real, c_pair_2], dim=1)
                            else:
                                real_cat = real
                                fake_cat = fake

                            y_fake, regr_fake = self._discriminator(fake_cat)
                            y_real, regr_real = self._discriminator(real_cat)

                            cos = nn.CosineSimilarity(dim=1, eps=1e-6)
                            fake_regr_loss = (1 - cos(regr_fake, sampled_label_emb))/2
                            real_regr_loss = (1 - cos(regr_real, sampled_label_emb))/2

                            # 1: fake, 0: real
                            rf_loss_d = -(torch.mean(y_real) - torch.mean(y_fake))
                            regr_loss_d = (torch.mean(fake_regr_loss) + torch.mean(real_regr_loss))/2
                            loss_d = loss_alpha * rf_loss_d + (1-loss_alpha) * regr_loss_d
     
                            #### DP ####
                            if self.private:
                                sigma = 1
                                weight_clip = 0.01 

                                if sigma is not None:
                                    for parameter in self._discriminator.parameters():
                                        parameter.register_hook(
                                            lambda grad: grad.cuda() + (1 / self._batch_size) * sigma
                                            * torch.randn(parameter.shape).cuda()
                                        )
                            #### DP ####

                            pen = self._discriminator.calc_gradient_penalty(
                                real_cat, fake_cat, self._device, self.pac)

                            optimizerD.zero_grad()
                            pen.backward(retain_graph=True) # https://machinelearningmastery.com/how-to-implement-wasserstein-loss-for-generative-adversarial-networks/ 
                            loss_d.backward()
                            optimizerD.step()

                            if self.private:
                                #### DP ####
                                # Weight clipping for privacy guarantee
                                for param in self._discriminator.parameters():
                                    param.data.clamp_(-weight_clip, weight_clip)
                                #### DP ####

                        fakez = torch.normal(mean=mean, std=std)
                        condvec_pair = self._data_sampler.sample_condvec_pair(self._batch_size)

                        if condvec_pair is None:
                            c_pair_1, m_pair_1, col_pair_1, opt_pair_1 = None, None, None, None
                        else:
                            c_pair_1, m_pair_1, col_pair_1, opt_pair_1 = condvec_pair
          
                            c_pair_1 = torch.from_numpy(c_pair_1).to(self._device)
                            m_pair_1 = torch.from_numpy(m_pair_1).to(self._device)
                            fakez = torch.cat([fakez, c_pair_1], dim=1)

                        sampled_label_emb = label_emb[torch.randint(0, label_emb.size(0), (self._batch_size,))]
                        fakez = torch.cat([fakez, sampled_label_emb], dim=1)  # Append vectors to be conditioned on to input features
            
                        fake = self._generator(fakez)
                        fakeact = self._apply_activate(fake)

                        if c_pair_1 is not None:
                            y_fake, regr_fake = self._discriminator(torch.cat([fakeact, c_pair_1], dim=1))
                        else:
                            y_fake, regr_fake = self._discriminator(fakeact)

                        if condvec_pair is None:
                            cross_entropy_pair = 0
                        else:
                            cross_entropy_pair = self._cond_loss_pair(fake, c_pair_1, m_pair_1)
                        
                        # 1: fake, 0: real
                        rf_loss_g = -torch.mean(y_fake) + cross_entropy_pair # + rules_penalty
                        regr_loss_g = (1 + cos(regr_fake, sampled_label_emb))/2

                        loss_g = loss_alpha * rf_loss_g + (1-loss_alpha) * regr_loss_g

                        optimizerG.zero_grad()
                        loss_g.backward()
                        optimizerG.step()
                    
                    if self._verbose:
                        ######## ADDED ########
                        now = datetime.now()
                        current_time = now.strftime("%H:%M:%S")

                        # Calculate the current privacy cost using the accountant
                        # https://github.com/BorealisAI/private-data-generation/blob/master/models/dp_wgan.py
                        # https://github.com/tensorflow/privacy/tree/master/tutorials/walkthrough

                        print(current_time, f"Epoch {i+1}, Loss G: {loss_g.detach().cpu(): .4f},"
                            f"Loss D: {loss_d.detach().cpu(): .4f}", flush=True)


                        if self.private:
                            orders = [1 + x / 10. for x in range(1, 100)]
                            sampling_probability = self._batch_size/len(train_data)
                            delta = 2e-6
                            rdp = compute_rdp(q=sampling_probability,
                                                noise_multiplier=sigma,
                                                steps=i * steps_per_epoch,
                                                orders=orders)
                            epsilon, _, opt_order = get_privacy_spent(orders, rdp, target_delta=delta) # target_delta=1e-5

                            print('differential privacy with eps = {:.3g} and delta = {}.'.format(
                                epsilon, delta))
                            print('The optimal RDP order is {}.'.format(opt_order))

                            if opt_order == max(orders) or opt_order == min(orders):
                                print('The privacy estimate is likely to be improved by expanding '
                                    'the set of orders.')
                        else:
                            epsilon = np.nan

                        
    def sample(self, label_emb, n, condition_column=None, condition_value=None):
        """Sample data similar to the training data.

        Choosing a condition_column and condition_value will increase the probability of the
        discrete condition_value happening in the condition_column.
        Args:
            n (int):
                Number of rows to sample.
            condition_column (string):cd
                Name of a discrete column.
            condition_value (string):
                Name of the category in the condition_column which we wish to increase the
                probability of happening.
        Returns:
            numpy.ndarray or pandas.DataFrame
        """
        n_total = n * label_emb.size(0)
        if condition_column is not None and condition_value is not None:
            condition_info = self._transformer.convert_column_name_value_to_id(
                condition_column, condition_value)
            global_condition_vec = self._data_sampler.generate_cond_from_condition_column_info(
                condition_info, self._batch_size)
        else:
            global_condition_vec = None


        steps = n_total // self._batch_size + 1
        label_ind = torch.arange(label_emb.size(0)).repeat_interleave(n)

        data = []
        for i in range(steps):
            batched_ind = label_ind[i * self._batch_size:(i+1)*self._batch_size]
            batched_label_emb = label_emb[batched_ind,:]

            mean = torch.zeros(batched_ind.size(0), self._embedding_dim)
            std = mean + 1
            fakez = torch.normal(mean=mean, std=std).to(self._device)

            if global_condition_vec is not None:
                condvec = global_condition_vec.copy()
            else:
                condvec = self._data_sampler.sample_original_condvec(self._batch_size)

            if condvec is None:
                pass
            else:
                c1 = condvec
                c1 = torch.from_numpy(c1).to(self._device)
                fakez = torch.cat([fakez, c1[:batched_ind.size(0)]], dim=1)
            
            fakez = torch.cat([fakez, batched_label_emb], dim=1)  # Append vectors to be conditioned on to input features

            fake = self._generator(fakez)
            fakeact = self._apply_activate(fake)
            data.append(fakeact.detach().cpu().numpy())

        data = np.concatenate(data, axis=0)
        data = data[:n]

        return self._transformer.inverse_transform(data)

    def set_device(self, device):
        self._device = device
        if self._generator is not None:
            self._generator.to(self._device)


    def xai_discriminator(self, data_samples):

        # for exlain AI (SHAP) the single row from the pd.DataFrame needs to be transformed. 
        data_samples = pd.DataFrame(data_samples).T

        condvec_pair = self._data_sampler.sample_condvec_pair(len(data_samples))
        c_pair_1, m_pair_1, col_pair_1, opt_pair_1 = condvec_pair

        if condvec_pair is None:
            c_pair_1, m_pair_1, col_pair_1, opt_pair_1 = None, None, None, None
            real = self._data_sampler.sample_data_pair(len(data_samples), col_pair_1, opt_pair_1)
        else:
            c_pair_1, m_pair_1, col_pair_1, opt_pair_1 = condvec_pair
            c_pair_1 = torch.from_numpy(c_pair_1).to(self._device)
            m_pair_1 = torch.from_numpy(m_pair_1).to(self._device)

            perm = np.arange(len(data_samples))
            np.random.shuffle(perm)

            real = self._data_sampler.sample_data_pair(len(data_samples), col_pair_1[perm], opt_pair_1[perm])
            c_pair_2 = c_pair_1[perm]

        real = torch.from_numpy(real.astype('float32')).to(self._device)
        
        if col_pair_1 is not None:
            real_cat = torch.cat([real, c_pair_2], dim=1)
        else:
            real_cat = real

        ### Wassertein distance?? (a data point from real training data's wassertain distance means what?)
        discriminator_predict_score = self._discriminator(real_cat)

        return discriminator_predict_score
