######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import warnings

warnings.filterwarnings("ignore")

import torch
import torch.nn as nn


def my_loss(output, target):
    loss = torch.sum(torch.abs(output - target))
    return loss


def count_parameters(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


class ANN_Model(nn.Module):
    def __init__(self, model_pt, gpu_mode):
        super(ANN_Model, self).__init__()
        if gpu_mode:
            self.mlp_model = torch.load(model_pt).cuda()
        else:
            self.mlp_model = torch.load(model_pt).cpu()
        self.gpu_mode = gpu_mode
        self.deactivate_dropout()

        self._get_named_modules()

    def _get_named_modules(self):
        self.named_modules = dict(self.mlp_model.named_modules())

    def _get_layer_obj(self, layer_name):
        return self.named_modules[layer_name]

    def get_dropout_dict(self):
        # Loop through and create a dict with dropout numbers and layer names
        ret_dict = {}
        for k, v in self.named_modules.items():
            if (isinstance(v, nn.Dropout)):
                ret_dict[k] = v.p

        return ret_dict

    def set_dropout_dict(self, dropout_dict):
        # Loop through and create a dict with dropout numbers and layer names
        for k, v in dropout_dict.items():
            print('Setting Dropout: %s --> %f' % (k, v))
            self.named_modules[k].p = v

    def get_layer_weights_bias(self, layer_name):
        # layer_obj = self.mlp_model.model.get_submodule(layer_name)
        layer_obj = self._get_layer_obj(layer_name)
        weight_orig = layer_obj.weight
        bias_orig = layer_obj.bias

        # Numpy weight and bias
        weight_orig_np = weight_orig.detach().cpu().numpy()
        bias_orig_np = bias_orig.detach().cpu().numpy()

        return weight_orig_np, bias_orig_np

    def set_layer_weights(self, layer_name, weights_np):
        # Access the layer by name and set the weight tensor
        layer_obj = self._get_layer_obj(layer_name)
        if (self.gpu_mode):
            layer_obj.weight = torch.nn.Parameter(torch.from_numpy(weights_np).cuda())
        else:
            layer_obj.weight = torch.nn.Parameter(torch.from_numpy(weights_np))
        return

    def set_layer_bias(self, layer_name, bias_np):
        # Access the layer by name and set the weight tensor
        layer_obj = self._get_layer_obj(layer_name)
        if (self.gpu_mode):
            layer_obj.bias = torch.nn.Parameter(torch.from_numpy(bias_np).cuda())
        else:
            layer_obj.bias = torch.nn.Parameter(torch.from_numpy(bias_np))

        return

    def freeze_layers(self, n_retain_layers):
        # List the modules
        params = list(self.mlp_model.parameters())

        # Each Layer has a weight and bias
        n_total = len(params)
        print('n_total: %d' % (n_total))
        for i_layer in range(0, n_total - 2 * n_retain_layers):
            if params[i_layer].requires_grad:
                params[i_layer].requires_grad = False
                print('Layer[%d] Grad True --> False' % (i_layer))
            else:
                print('Layer[%d] Grad False Already' % (i_layer))

    def activate_dropout(self):
        self.dropout_mode = True
        self.mlp_model = self.mlp_model.train()

    def deactivate_dropout(self):
        self.dropout_mode = False
        self.mlp_model = self.mlp_model.eval()

    # Evaluate the forward pass without no_grad
    # Convert the return to numpy
    def forward(self, x):
        with torch.no_grad():
            cur_model_eval = self.mlp_model(x)
            cur_model_eval_np = cur_model_eval.detach().cpu().numpy()
            return cur_model_eval_np
