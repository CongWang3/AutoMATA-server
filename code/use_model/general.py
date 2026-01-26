import shutup 
shutup.please()

import math
import warnings
import numpy as np
import torch.optim
import torchvision
from torch.utils.data import DataLoader, SubsetRandomSampler
# from matplotlib import pyplot as plt
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix
from sklearn.utils import shuffle
from utils.minisom import MiniSom
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_recall_fscore_support
import pandas as pd
from torch import nn, optim
import torch.nn.functional as F
from torch.nn import Linear, ReLU, Sigmoid, Module, BCELoss, Softmax
from torch.nn.init import kaiming_uniform_, xavier_uniform_
from sklearn.model_selection import  StratifiedKFold
# from torch.utils.tensorboard import SummaryWriter
import pandas as pd
import os
os.environ['CUDA_VISIBLE_DEVICES'] ='1'  # 参数待改
import torch
from sklearn.metrics import accuracy_score,recall_score,precision_score,f1_score,matthews_corrcoef,confusion_matrix,roc_auc_score,classification_report,multilabel_confusion_matrix,hamming_loss
from utils.plot_utils import plotfig
from utils.earlystopping import EarlyStopping 
from utils.FocalLoss import FocalLoss

warnings.simplefilter(action='ignore', category=RuntimeWarning)



import argparse
import pickle

from DataProcess import load_data



def test(dataloader, model):
    model.eval()
    true_label_list, pred_label_list, probability_list= [], [], []

    with torch.no_grad():
        for X, y in dataloader:
            if model_type == "LSTM" or model_type == "RNN":
                X, y = X.unsqueeze(1).to(device), y.to(device)
            else:
                X, y = X.to(device), y.to(device) 
            pred = model(X)

            # 一审 计算各类概率并提取最大概率与其对应标签
            if hasattr(model, 'loss_function') and model.loss_function == 'nllloss':
                probs = pred.exp()
            else:
                probs = F.softmax(pred, dim=1)
            max_prob, max_idx = probs.max(dim=1)

            true_label_list.append(y.cpu().detach().numpy())
            pred_label_list.append(pred.argmax(dim=1).cpu().detach().numpy())
            probability_list.append(pred[:,1].cpu().detach().numpy())

    y_true = np.concatenate(true_label_list)
    y_pred = np.concatenate(pred_label_list)
    y_prob = np.concatenate(probability_list)
    acc = accuracy_score(y_true,y_pred)
    precision, recall, f1 = precision_recall_fscore_support(y_true, y_pred, average='macro')[:-1]

    return acc, precision, recall, f1, y_prob, y_pred

def extract_features(autoencoder, dataloader):
    encoder = autoencoder.encoder
    features = []
    labels = []
    for data in dataloader:
        inputs, label = data
        inputs, label  = inputs.to(device), label.to(device)
        with torch.no_grad():
            encoded_features = encoder(inputs)
        features.append(encoded_features)
        labels.append(label)

    features = torch.cat(features, dim=0) 
    labels = torch.cat(labels, dim=0) 

    dataset =  torch.utils.data.TensorDataset(features, labels)
    loader = DataLoader(dataset=dataset, batch_size=batch_size, shuffle=True)
    return loader


def test_autoencoder(dataloader, autoencoder, classifier):
    loader = extract_features(autoencoder, dataloader) 
    true_label_list, pred_label_list, probability_list= [], [], []

    classifier.eval()
    with torch.no_grad():
        for data in loader:
            features, labels = data[0].to(device), data[1].to(device)
            outputs = classifier(features)
            # 一审 计算各类概率并提取最大概率与其对应标签
            if hasattr(classifier, 'loss_function') and model.loss_function == 'nllloss':
                probs = outputs.exp()
            else:
                probs = F.softmax(outputs, dim=1)
            max_prob, max_idx = probs.max(dim=1)

            true_label_list.append(labels.cpu().detach().numpy())
            pred_label_list.append(outputs.argmax(dim=1).cpu().detach().numpy())
            probability_list.append(outputs[:,1].cpu().detach().numpy())

    y_true = np.concatenate(true_label_list)
    y_pred = np.concatenate(pred_label_list)
    y_prob = np.concatenate(probability_list)

    acc = accuracy_score(y_true,y_pred)
    precision, recall, f1 = precision_recall_fscore_support(y_true, y_pred, average='macro')[:-1]

    return acc, precision, recall, f1, y_prob, y_pred  # 一审



class Autoencoder(nn.Module): 
    def __init__(self, input_dim, hidden_size_1=64, hidden_size_2=32, hidden_size_3=16, lr=0.001, dropout_rate=0.5):
        super(Autoencoder, self).__init__()

        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_size_1),
            nn.ReLU(True),
            nn.Dropout(dropout_rate),
            nn.Linear(hidden_size_1, hidden_size_2),
            nn.ReLU(True),
            nn.Linear(hidden_size_2, hidden_size_3),
            nn.ReLU(True)
        )
        self.decoder = nn.Sequential(
            nn.Linear(hidden_size_3, hidden_size_2),
            nn.ReLU(True),
            nn.Linear(hidden_size_2, hidden_size_1),
            nn.ReLU(True),
            nn.Linear(hidden_size_1, input_dim),
        )

        self.criterion = nn.MSELoss() 
        self.learning_rate = lr
        self.optimizer = optim.Adam(self.parameters(), lr=self.learning_rate)

    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded, encoded


class Classifier(nn.Module):
    def __init__(self, hidden_size_3=16, cls_hidden_size=8, output_size=2, lr=0.001, loss_function="crossentropy", optimizer_function="adam"):
        self.output_size = output_size 
        super(Classifier, self).__init__()

        self.fc = nn.Sequential(
            nn.Linear(hidden_size_3, cls_hidden_size),
            nn.ReLU(),
            nn.Linear(cls_hidden_size, output_size),
        )

        self.learning_rate = lr
        self.loss_function = loss_function  # 一审
        if loss_function == "crossentropy":
            self.criterion = nn.CrossEntropyLoss()
        elif loss_function == "focalloss":
            if output_size == 2:
                self.criterion = FocalLoss(gamma=2, alpha=0.25, task_type='binary')
            else:
                self.criterion = FocalLoss(gamma=2, alpha=0.25, task_type='multi-class', num_classes=output_size)
        elif loss_function == "nllloss":
            self.criterion = nn.NLLLoss()

        if optimizer_function == "adam":
            self.optimizer = optim.Adam(self.parameters(), lr=self.learning_rate)
        elif optimizer_function == "sgd":
            self.optimizer = optim.SGD(self.parameters(), lr=self.learning_rate, momentum=0)  # 应改为0.5 SGD对这些敏感
        elif optimizer_function == "rmsprop":
            self.optimizer = optim.RMSprop(self.parameters(), lr=self.learning_rate)

    def forward(self, x):
        # 一审
        logits = self.fc(x)
        if self.loss_function == "nllloss":
            return nn.functional.log_softmax(logits, dim=1)
        return logits
        # if (self.output_size == 2):
        #     act = nn.Softmax(dim=1).to(device)
        #     x = act(x)
        # return self.fc(x)

class LSTMModel(nn.Module):
    def __init__(self, input_size, hidden_size, output_size, num_layers=1):
        super(LSTMModel, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)
        self.output_size = output_size


        self.learning_rate = lr
        self.loss_function = loss_function  # 一审
        if loss_function == "crossentropy":
            self.criterion = nn.CrossEntropyLoss()
        elif loss_function == "focalloss":
            if output_size == 2:
                self.criterion = FocalLoss(gamma=2, alpha=0.25, task_type='binary')
            else:
                self.criterion = FocalLoss(gamma=2, alpha=0.25, task_type='multi-class', num_classes=output_size)
        elif loss_function == "nllloss":
            self.criterion = nn.NLLLoss()

        if optimizer_function == "adam":
            self.optimier = optim.Adam(self.parameters(), lr=self.learning_rate)
        elif optimizer_function == "sgd":
            self.optimier = optim.SGD(self.parameters(), lr=self.learning_rate, momentum=0)
        elif optimizer_function == "rmsprop":
            self.optimier = optim.RMSprop(self.parameters(), lr=self.learning_rate)
 
    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        out, _ = self.lstm(x, (h0, c0))
        out = self.fc(out[:, -1, :])

        # 一审
        if self.loss_function == "nllloss":
            return F.log_softmax(out, dim=1)
        return out

        # if (self.output_size == 2):
        #     act = nn.Softmax(dim=1).to(device)
        #     out = act(out)

        # return out

class Cnn(nn.Module):
    def __init__(self, conv_size_1=64, conv_size_2=32, output_size=2, dropout_rate=0.0, lr=0.001, loss_function="crossentropy", optimizer_function="adam"):
        super(Cnn, self).__init__()
        self.output_size = output_size
        self.model1 = nn.Sequential(
            nn.Conv1d(1, conv_size_1, 2, stride=2, padding=6),  # nn.Conv1d(in_channels, out_channels, kernel_size
            nn.ReLU(),
            nn.MaxPool1d(2), 
        )

        self.model2 = nn.Sequential(
            nn.Conv1d(conv_size_1, conv_size_2, 2, padding=6),
            nn.ReLU(),
            nn.MaxPool1d(4), 
            nn.Flatten(),
            nn.Dropout(dropout_rate)
        )
        
        self.learning_rate = lr
        self.loss_function = loss_function  # 一审
        self.fc = nn.LazyLinear(self.output_size)  # 一审
        if loss_function == "crossentropy":
            self.criterion = nn.CrossEntropyLoss()
        elif loss_function == "focalloss":
            if output_size == 2:
                self.criterion = FocalLoss(gamma=2, alpha=0.25, task_type='binary')
            else:
                self.criterion = FocalLoss(gamma=2, alpha=0.25, task_type='multi-class', num_classes=output_size)
        elif loss_function == "nllloss":
            self.criterion = nn.NLLLoss()

        if optimizer_function == "adam":
            self.optimier = optim.Adam(self.parameters(), lr=self.learning_rate)
        elif optimizer_function == "sgd":
            self.optimier = optim.SGD(self.parameters(), lr=self.learning_rate, momentum=0)
        elif optimizer_function == "rmsprop":
            self.optimier = optim.RMSprop(self.parameters(), lr=self.learning_rate)

    def forward(self, input):
        input = input.reshape(-1,1,input.shape[1])   #结果为torch.Size([34, 1, 4])  目的是把二维变为三维数据
        x = self.model1(input)
        x = self.model2(x)
        # 一审
        logits = self.fc(x)
        if self.loss_function == "nllloss":
            return nn.functional.log_softmax(logits, dim=1)
        return logits



class MLPModel(nn.Module):
    def __init__(self, n_inputs,  linear_size_1, linear_size_2, output_size, dropout_rate, lr, loss_function, optimizer_function):
        super(MLPModel, self).__init__()
        self.output_size = output_size 
        self.hidden1 = Linear(n_inputs, linear_size_1)
        kaiming_uniform_(self.hidden1.weight, nonlinearity='relu')
        self.act1 = ReLU()
        self.hidden2 = Linear(linear_size_1, linear_size_2)
        kaiming_uniform_(self.hidden2.weight, nonlinearity='relu')
        self.act2 = ReLU()
        self.dropout = nn.Dropout(dropout_rate)
        self.hidden3 = Linear(linear_size_2, output_size) 
        xavier_uniform_(self.hidden3.weight)

        self.learning_rate = lr
        self.loss_function = loss_function  # 一审

        if loss_function == "crossentropy":
            self.criterion = nn.CrossEntropyLoss()
        elif loss_function == "focalloss":
            if output_size == 2:
                self.criterion = FocalLoss(gamma=2, alpha=0.25, task_type='binary')
            else:
                self.criterion = FocalLoss(gamma=2, alpha=0.25, task_type='multi-class', num_classes=output_size)
        elif loss_function == "nllloss":
            self.criterion = nn.NLLLoss()

        if optimizer_function == "adam":
            self.optimier = optim.Adam(self.parameters(), lr=self.learning_rate)
        elif optimizer_function == "sgd":
            self.optimier = optim.SGD(self.parameters(), lr=self.learning_rate, momentum=0)
        elif optimizer_function == "rmsprop":
            self.optimier = optim.RMSprop(self.parameters(), lr=self.learning_rate)
 
    def forward(self, X):
        X = self.hidden1(X)
        X = self.act1(X)
        X = self.hidden2(X)
        X = self.act2(X)
        X = self.dropout(X)
        X = self.hidden3(X)
        # 一审
        if self.loss_function == "nllloss":
            return F.log_softmax(X, dim=1)
        return X


class RBFN(nn.Module):
    def __init__(self,centers_dim,out_dim,centers,sigma):
        super(RBFN,self).__init__()
        self.flatten = nn.Flatten()#变成二维的
        self.centers_dim=centers_dim
        self.out_dim=out_dim
        self.centers = nn.Parameter(centers)
        self.sigma = nn.Parameter(sigma)
        self.linear = nn.Linear(self.centers_dim, self.out_dim)

        self.learning_rate = lr
        self.loss_function = loss_function  # 一审

        if loss_function == "crossentropy":
            self.criterion = nn.CrossEntropyLoss()
        elif loss_function == "focalloss":
            if out_dim == 2:
                self.criterion = FocalLoss(gamma=2, alpha=0.25, task_type='binary')
            else:
                self.criterion = FocalLoss(gamma=2, alpha=0.25, task_type='multi-class', num_classes=out_dim)
        elif loss_function == "nllloss":
            self.criterion = nn.NLLLoss()

        if optimizer_function == "adam":
            self.optimier = optim.Adam(self.parameters(), lr=self.learning_rate)
        elif optimizer_function == "sgd":
            self.optimier = optim.SGD(self.parameters(), lr=self.learning_rate, momentum=0)
        elif optimizer_function == "rmsprop":
            self.optimier = optim.RMSprop(self.parameters(), lr=self.learning_rate)
 
    def forward(self,X):
        x= self.flatten(X)
        distance = torch.cdist(x, self.centers)
        gauss = torch.exp(-distance ** 2 / (2 * self.sigma ** 2))
        y=self.linear(gauss)
        
        # 一审
        if self.loss_function == "nllloss":
            return nn.functional.log_softmax(y, dim=1)
        return y
    

class RNNModel(nn.Module):
    def __init__(self, input_size, hidden_size, output_size, num_layers=1):
        super(RNNModel, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.rnn = nn.RNN(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)
        self.output_size = output_size

        self.learning_rate = lr
        self.loss_function = loss_function  # 一审

        if loss_function == "crossentropy":
            self.criterion = nn.CrossEntropyLoss()
        elif loss_function == "focalloss":
            if output_size == 2:
                self.criterion = FocalLoss(gamma=2, alpha=0.25, task_type='binary')
            else:
                self.criterion = FocalLoss(gamma=2, alpha=0.25, task_type='multi-class', num_classes=output_size)
            
        elif loss_function == "nllloss":
            self.criterion = nn.NLLLoss()
            print('nono')

        if optimizer_function == "adam":
            self.optimier = optim.Adam(self.parameters(), lr=self.learning_rate)
        elif optimizer_function == "sgd":
            self.optimier = optim.SGD(self.parameters(), lr=self.learning_rate, momentum=0)
        elif optimizer_function == "rmsprop":
            self.optimier = optim.RMSprop(self.parameters(), lr=self.learning_rate)
 
    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        out, hidden = self.rnn(x, h0)
        out = self.fc(out[:, -1, :])

        # 一审
        if self.loss_function == "nllloss":
            return F.log_softmax(out, dim=1)
        return out


# 定义PositionalEncoding
class PositionalEncoding(nn.Module):
    def __init__(self, d_model, dropout, max_len=5000):
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)
        
        # pe的维度(位置编码最大长度，模型维度)
        pe = torch.zeros(max_len, d_model)
        # 维度为（max_len, 1）：先在[0,max_len]中取max_len个整数，再加一个维度
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        # 位置编码的除数项：10000^(2i/d_model)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-np.log(10000.0) / d_model))
        # sin负责奇数；cos负责偶数
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        
        #维度变换：(max_len,d_model)→(1,max_len,d_model)→(max_len,1,d_model)
        pe = pe.unsqueeze(0).transpose(0, 1)
        # 将pe注册为模型缓冲区
        self.register_buffer('pe', pe)
        
        
    def forward(self, x):
        # 取pe的前x.size(0)行，即
        # (x.size(0),1,d_model) → (x.size(0),d_model)，拼接到x上
        x = x + self.pe[:x.size(0), :]
        return self.dropout(x)



# 定义Transformer模型
class TransformerModel(nn.Module):
    def __init__(self, input_dim, output_size, d_model, nhead, num_layers, dim_feedforward, dropout, loss_function, optimizer_function):
        self.output_size = output_size  # 记录flatten层的输出维度——分类数
        super(TransformerModel, self).__init__()
        # 创建一个线性变换层，维度input_dim4→d_model
        # self.embedding = nn.Embedding(input_dim, d_model)  # 使用嵌入层 一个input_dim维的样本用d_model维表示, Embedding必须用整型数据，不能用float数据
        self.embedding = nn.Linear(input_dim, d_model)
        # 生成pe
        self.pos_encoder = PositionalEncoding(d_model, dropout)
        # 生成一层encoder
        encoder_layers = nn.TransformerEncoderLayer(d_model=d_model, nhead=nhead, dim_feedforward=dim_feedforward, dropout=dropout)
        # 多层encoder
        self.transformer_encoder = nn.TransformerEncoder(encoder_layers, num_layers=num_layers)
        # 维度d_model→output_dim
        self.fc = nn.Linear(d_model, output_size)
        self.d_model = d_model

        self.softmax = nn.Softmax(dim=1)

        self.learning_rate = lr
        self.loss_function = loss_function

        if loss_function == "crossentropy":
            self.criterion = nn.CrossEntropyLoss()
        elif loss_function == "focalloss":
            if output_size == 2:
                self.criterion = FocalLoss(gamma=2, alpha=0.25, task_type='binary')
            else:
                self.criterion = FocalLoss(gamma=2, alpha=0.25, task_type='multi-class', num_classes=output_size)
        elif loss_function == "nllloss":
            self.criterion = nn.NLLLoss()

        if optimizer_function == "adam":
            self.optimier = optim.Adam(self.parameters(), lr=self.learning_rate)
        elif optimizer_function == "sgd":
            self.optimier = optim.SGD(self.parameters(), lr=self.learning_rate, momentum=0)
        elif optimizer_function == "rmsprop":
            self.optimier = optim.RMSprop(self.parameters(), lr=self.learning_rate)
 

    def forward(self, src):
        src = self.embedding(src) 
        src = self.pos_encoder(src) 
        output = self.transformer_encoder(src) 
        output = output.permute(1, 0, 2) 
        output = torch.mean(output, dim=1) 
        output = self.fc(output) 

        # 一审
        if self.loss_function == "nllloss":
            return F.log_softmax(output, dim=1)
        return output



if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--jobID", default="20250416150624_agTW5its", type=str)
    parser.add_argument("--model_type", default="Transformer", type=str)
    args = parser.parse_args()

    jobID = args.jobID
    model_type = args.model_type
    batch_size = 128

    print('jobID =',jobID)
    print('model_type =',args.model_type)


    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


    '''加载模型'''
    # "CNN", "LSTM", "RNN", "MLP", "AutoEncoder", "Transformer", "SOM", "RBFN")
    savename = '/xp/www/AutoMATA/download_data/Jobs/'+jobID+'/model.pth'
    if (model_type == 'AutoEncoder'):
        savename = '/xp/www/AutoMATA/download_data/Jobs/'+jobID+'/model_autoencoder.pth'
        checkpoint = torch.load(savename)
        input_dim = checkpoint['input_dim']
        hidden_size_1 = checkpoint['hidden_size_1']
        hidden_size_2 = checkpoint['hidden_size_2']
        hidden_size_3 = checkpoint['hidden_size_3']
        lr = checkpoint['learning_rate']
        dropout_rate = checkpoint['dropout_rate']
        encoder = Autoencoder(input_dim, hidden_size_1, hidden_size_2, hidden_size_3, lr, dropout_rate)
        encoder.load_state_dict(checkpoint['model_state_dict'])

        savename_cls = '/xp/www/AutoMATA/download_data/Jobs/'+jobID+'/model_cls.pth'
        checkpoint_cls = torch.load(savename_cls)
        cls_hidden_size = checkpoint_cls['cls_hidden_size']
        output_size = checkpoint_cls['output_size']
        loss_function = checkpoint_cls['loss_function']
        optimizer_function = checkpoint_cls['optimizer_function']
        classifier = Classifier(hidden_size_3, cls_hidden_size, output_size, lr, loss_function, optimizer_function)
        classifier.load_state_dict(checkpoint_cls['model_state_dict'])

    elif (model_type == 'CNN'):
        checkpoint = torch.load(savename)
        input_size = checkpoint['input_size']
        loss_function = checkpoint['loss_function']
        optimizer_function = checkpoint['optimizer_function']
        output_size = checkpoint['output_size']
        lr = checkpoint['learning_rate']
        dropout_rate = checkpoint['dropout_rate']
        conv_size_1 = checkpoint['conv_size_1']
        conv_size_2 = checkpoint['conv_size_2']

        print(loss_function)

        model = Cnn(conv_size_1, conv_size_2, output_size, dropout_rate, lr, loss_function, optimizer_function)
        model.load_state_dict(checkpoint['model_state_dict'])

    elif (model_type == 'LSTM'):
        checkpoint = torch.load(savename)
        loss_function = checkpoint['loss_function']
        optimizer_function = checkpoint['optimizer_function']
        output_size = checkpoint['output_size']
        input_size = checkpoint['input_size']
        hidden_size = checkpoint['hidden_size']
        num_layers = checkpoint['num_layers']
        lr = checkpoint['learning_rate']
        model = LSTMModel(input_size, hidden_size, output_size, num_layers).to(device)
        model.load_state_dict(checkpoint['model_state_dict'])

    elif (model_type == 'MLP'):
        checkpoint = torch.load(savename)
        loss_function = checkpoint['loss_function']
        optimizer_function = checkpoint['optimizer_function']
        output_size = checkpoint['output_size']
        input_size = checkpoint['input_size']
        linear_size_1 = checkpoint['linear_size_1']
        linear_size_2 = checkpoint['linear_size_2']
        lr = checkpoint['learning_rate']
        dropout_rate = checkpoint['dropout_rate']
        model = MLPModel(input_size, linear_size_1, linear_size_2, output_size, dropout_rate, lr, loss_function, optimizer_function).to(device)
        model.load_state_dict(checkpoint['model_state_dict'])

    elif (model_type == 'RBFN'):
        checkpoint = torch.load(savename)
        loss_function = checkpoint['loss_function']
        optimizer_function = checkpoint['optimizer_function']
        out_dim = checkpoint['out_dim']
        input_dim = checkpoint['input_dim']
        centers_dim = checkpoint['centers_dim']
        centers = checkpoint['centers']
        lr = checkpoint['learning_rate']
        sigma = checkpoint['sigma']
        model = RBFN(centers_dim,out_dim,centers,sigma).to(device)
        model.load_state_dict(checkpoint['model_state_dict'])

    elif (model_type == 'RNN'):
        checkpoint = torch.load(savename)
        loss_function = checkpoint['loss_function']
        optimizer_function = checkpoint['optimizer_function']
        output_size = checkpoint['output_size']
        input_size = checkpoint['input_size']
        hidden_size = checkpoint['hidden_size']
        num_layers = checkpoint['num_layers']
        lr = checkpoint['learning_rate']
        model = RNNModel(input_size, hidden_size, output_size, num_layers).to(device)
        model.load_state_dict(checkpoint['model_state_dict'])

    elif (model_type == 'Transformer'):
        checkpoint = torch.load(savename)
        loss_function = checkpoint['loss_function']
        optimizer_function = checkpoint['optimizer_function']
        output_size = checkpoint['output_size']
        input_dim = checkpoint['input_dim']
        dropout = checkpoint['dropout']
        d_model = checkpoint['d_model']
        nhead = checkpoint['nhead']
        num_layers = checkpoint['num_layers']
        dim_feedforward = checkpoint['dim_feedforward']
        lr = checkpoint['learning_rate']
        model = TransformerModel(input_dim, output_size, d_model, nhead, num_layers, dim_feedforward, dropout, loss_function, optimizer_function)
        model.load_state_dict(checkpoint['model_state_dict'])


    '''load testing data'''
    X_test, Y_test, name = load_data("test", jobID=jobID)
    test_dataset =  torch.utils.data.TensorDataset(X_test, Y_test)
    test_loader = DataLoader(dataset=test_dataset, batch_size=batch_size, shuffle=False)

    # 一审
    if (model_type == 'AutoEncoder'):
        acc, precision, recall, f1, y_prob, y_pred = test_autoencoder(dataloader=test_loader, autoencoder = encoder, classifier = classifier)
    else:
        acc, precision, recall, f1, y_prob, y_pred = test(dataloader=test_loader, model=model)
    print("test acc = {}, precision = {}, recall = {}, f1 = {}".format(acc, precision, recall, f1))

    '''保存使用本模型测试结果指标'''
    with open("/xp/www/AutoMATA/download_data/Jobs/"+jobID+"/result/test_metrics_result.txt", mode="w") as f:
        f.write("test result: \n")
        f.write("acc = " + str(acc) + "\n")
        f.write("precision = " + str(precision) + "\n")
        f.write("recall = " + str(recall) + "\n")
        f.write("f1 = " + str(f1) + "\n")


    '''保存使用本模型的测试结果'''
    with open("/xp/www/AutoMATA/download_data/Jobs/"+jobID+"/result/test_result.txt", mode="w") as f:
        # 一审
        f.write("name" + "\t" + "max_probability" + "\t" + "predicted_label" + "\n")
        for i in range(len(name)):
            f.write(name[i] + "\t" + str(y_prob[i]) + "\t" + str(y_pred[i]) + "\n")
        # f.write("name" + "\t" + "probability" + "\n")
        # for i in range(len(name)):
        #     f.write(name[i] + "\t" + str(y_prob[i]) + "\n")
