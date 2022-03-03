######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import warnings

warnings.filterwarnings("ignore")

import torch
from torch.autograd import Variable
import torch.nn as nn
import torch.optim as optim

def my_loss(output, target):
    loss = torch.sum(torch.abs(output - target))
    return loss

class MLP(nn.Module):
    def __init__(self, n_input=1, n_output=1, hidden_layers=[100, 50, 20, 10, 5, 1], droprate=0.2, activation='relu'):
        super(MLP, self).__init__()
        self.model = nn.Sequential()
        self.model.add_module('input', nn.Linear(n_input, hidden_layers[0]))
        if activation == 'relu':
            self.model.add_module('relu0', nn.ReLU())
        elif activation == 'tanh':
            self.model.add_module('tanh0', nn.Tanh())
        else:
            self.model.add_module('sigmoid0', nn.Sigmoid())
        for i in range(len(hidden_layers) - 1):
            self.model.add_module('dropout' + str(i + 1), nn.Dropout(p=droprate))
            self.model.add_module('hidden' + str(i + 1), nn.Linear(hidden_layers[i], hidden_layers[i + 1]))
            if activation == 'relu':
                self.model.add_module('relu' + str(i + 1), nn.ReLU())
            elif activation == 'tanh':
                self.model.add_module('tanh' + str(i + 1), nn.Tanh())
            else:
                self.model.add_module('sigmoid' + str(i + 1), nn.Sigmoid())

        self.model.add_module('dropout' + str(i + 2), nn.Dropout(p=droprate))
        self.model.add_module('final', nn.Linear(hidden_layers[i + 1], n_output))

    def freeze_layers(self, n_retain_layers):
        # List the modules
        params = list(self.model.parameters())

        # Each Layer has a weight and bias
        n_total = len(params)
        for i_layer in range(0, n_total - 2 * n_retain_layers):
            if params[i_layer].requires_grad:
                params[i_layer].requires_grad = False
                print('Layer[%d] Grad True --> False')
            else:
                print('Layer[%d] Grad False Already')

    def forward(self, x):
        return self.model(x)


class MLPRegressor:
    def __init__(self, n_input=1, n_output=1, hidden_layers=[100, 50, 20, 10, 5, 1], droprate=0.2, activation='relu',
                 max_epoch=1000, lr=0.001,
                 weight_decay=1e-6, gpu_mode=False):
        self.max_epoch = max_epoch
        self.lr = lr
        self.mlp_model = MLP(n_input=n_input, n_output=n_output, hidden_layers=hidden_layers, droprate=droprate,
                         activation=activation)
        self.gpu_mode = gpu_mode
        self.weight_decay = weight_decay

        if (self.gpu_mode > 0):
            self.mlp_model.cuda()

        self.optimizer = optim.Adam(filter(lambda p: p.requires_grad, self.mlp_model.parameters()), lr=self.lr, weight_decay=self.weight_decay)

    def freeze_layers(self, n_retain_layers):
        # Relay the call to the model and set the optimizer
        self.mlp_model.freeze_layers(n_retain_layers=n_retain_layers)
        if (self.gpu_mode):
            self.mlp_model.cuda()
        self.optimizer = optim.Adam(filter(lambda p: p.requires_grad, self.mlp_model.parameters()), lr=self.lr, weight_decay=self.weight_decay)

    def fit(self, X_train, y_train, X_test, y_test, verbose=True):
        X_train_pt = Variable(torch.from_numpy(X_train).type(torch.FloatTensor))
        y_train_pt = Variable(torch.from_numpy(y_train).type(torch.FloatTensor))
        X_test_pt = Variable(torch.from_numpy(X_test).type(torch.FloatTensor))
        y_test_pt = Variable(torch.from_numpy(y_test).type(torch.FloatTensor))

        if (self.gpu_mode):
            X_train_pt = X_train_pt.cuda()
            y_train_pt = y_train_pt.cuda()
            X_test_pt = X_test_pt.cuda()
            y_test_pt = y_test_pt.cuda()

        loss_history = []
        for epoch in range(self.max_epoch):
            self.optimizer.zero_grad()
            outputs = self.mlp_model(X_train_pt)
            loss = my_loss(outputs, y_train_pt)
            loss.backward()
            self.optimizer.step()

            with torch.no_grad():
                # Set to evaluation mode
                val_outputs = self.mlp_model(X_test_pt)
                val_loss = my_loss(val_outputs, y_test_pt)

            if verbose:
                print('Epoch {} loss: {}, val_loss: {}'.format(epoch + 1, loss.item(), val_loss.item()))
                loss_history.append((loss.item(), val_loss.item()))

        return loss_history
