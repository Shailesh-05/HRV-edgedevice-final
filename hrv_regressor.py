from networks import regressor
from data_utils import read_freq_data, SignalDataset
from torch.utils.data import random_split
import torchvision.transforms as transforms
import torch
import argparse
import json
import tensorflow as tf
import numpy as np
import pandas as pd

#HRV Regressor model

class HrvRegressor:
    def __init__(self, config, model_type="siren"):
        # load data
        torch.manual_seed(1)
        input_signal, output_signal, self.labels = read_freq_data(config["folder_path"])
        full_dataset = SignalDataset(input_signal, output_signal, self.labels, transforms.ToTensor())
        train_set, val_set, test_set = random_split(full_dataset, [650, 194, 195])
        ann_upsampler = torch.load(config["upsampler_path"])
        hrv_data = pd.read_csv(config["hrv_data"]).to_numpy()
        get_input = lambda x: np.array([ann_upsampler(inp.float()).detach().numpy() for inp, op, label in x])
        get_label = lambda x: np.array([hrv_data[i] for i in x.indices])

        self.train_input, self.train_labels = get_input(train_set), get_label(train_set)
        self.val_input, self.val_labels = get_input(val_set), get_label(val_set)
        self.test_input, self.test_labels = get_input(test_set), get_label(test_set)
        self.regressor_net = regressor.regressor_network_siren(output_signal.shape) if model_type=="siren" else  regressor.regressor_network(output_signal.shape)
        self.regressor_net.compile(loss=tf.keras.losses.MeanSquaredError(), optimizer='adam',metrics=['mae','mse','mape'])

    def train(self):
        history = self.regressor_net.fit(self.train_input, self.train_labels,validation_data=(self.val_input, self.val_labels) ,batch_size = 32, epochs = 1000)
        test_loss = self.regressor_net.evaluate(self.test_input,self.test_labels)
        print("Test Loss")
        print(test_loss)
        print("Val Loss")
        print(history.history['val_loss'])

        
        
        
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='HRV Regressor Training')
    parser.add_argument('--config', help="path to config with training params", default="config.json")
    args = parser.parse_args()
    config=json.load(open(args.config, 'r'))
    trainer =  HrvRegressor(config=config)
    trainer.train()
    








