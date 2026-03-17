# 使用pt36
# 参数待改——web提交的参数
# lstm: https://blog.csdn.net/qq_27353441/article/details/139753699

import shutup  # 控制台输出 忽略 warning
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
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_recall_fscore_support
import pandas as pd
from torch import nn, optim
import torch.nn.functional as F
from utils.FocalLoss import FocalLoss
from sklearn.model_selection import  StratifiedKFold
import pandas as pd
import os
os.environ['CUDA_VISIBLE_DEVICES'] ='1'  # 参数待改
import torch
from sklearn.metrics import accuracy_score,recall_score,precision_score,f1_score,matthews_corrcoef,confusion_matrix,roc_auc_score,classification_report,multilabel_confusion_matrix,hamming_loss
from utils.plot_utils import plotfig
from utils.earlystopping import EarlyStopping  # 保存性能最好的模型torch.save

warnings.simplefilter(action='ignore', category=RuntimeWarning)
torch.manual_seed(2022)

import argparse
import pickle


from DataProcess import load_data,process


def train(dataloader, model):
    model.train()
    num_batches = len(dataloader)
    train_loss= 0 # 积累训练损失
    true_label_list, pred_label_list= [], []

    for data in dataloader:
        X_data, Y_data = data[0].unsqueeze(1).to(device), data[1].to(device)  # 把训练数据集和标签传入cpu或GPU, unsqueeze(1)增加序列维度
        output = model(X_data)  # 自动初始化 w权值
        
        loss = model.criterion(output, Y_data)  # label.squeeze().long() # 通过交叉熵损失函数计算损失值loss

        train_loss += loss.item()  # 计算损失
        true_label_list.append(Y_data.cpu().detach().numpy())
        pred_label_list.append(output.argmax(dim=1).cpu().detach().numpy())
        # Backpropagation 进来一个batch的数据，计算一次梯度，更新一次网络
        model.optimier.zero_grad()  # 梯度值清零
        loss.backward()  # 反向传播计算得到每个参数的梯度值
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)  # 添加梯度裁剪，防止梯度爆炸
        model.optimier.step()  # 根据梯度更新网络参数

    y_true = np.concatenate(true_label_list)
    y_pred = np.concatenate(pred_label_list)
    train_loss /= num_batches  # 计算平均损失（一次迭代的损失）
    train_acc = accuracy_score(y_true,y_pred)
    train_precision, train_recall, train_f1 = precision_recall_fscore_support(y_true, y_pred, average='weighted')[:-1]

    return train_loss, train_acc, train_precision, train_recall, train_f1


def validate(dataloader, model):
    size = len(dataloader.dataset)  # 数据集总样本数
    num_batches = len(dataloader)  # 批次数量（多少批）
    # print('num_batches =', num_batches)
    model.eval()
    val_loss = 0 # 积累测试损失
    true_label_list, pred_label_list= [], []

    with torch.no_grad(): # 上下文管理器，将其包裹的代码块中的梯度计算禁用，以减少内存使用和加速计算。
        for X, y in dataloader:
            X, y = X.unsqueeze(1).to(device), y.to(device)  # #将测试数据移动到指定的设备，以确保与模型的设备匹配。
            pred = model(X)
            val_loss += model.criterion(pred, y).item() #计算并累积测试损失
            true_label_list.append(y.cpu().detach().numpy())
            pred_label_list.append(pred.argmax(dim=1).cpu().detach().numpy())

    y_true = np.concatenate(true_label_list)
    y_pred = np.concatenate(pred_label_list)
    val_loss /= num_batches  # 计算平均损失（一次迭代的损失）
    val_acc = accuracy_score(y_true,y_pred)
    val_precision, val_recall, val_f1 = precision_recall_fscore_support(y_true, y_pred, average='weighted')[:-1]

    return val_loss, val_acc, val_precision, val_recall, val_f1

def test(dataloader, model):
    size = len(dataloader.dataset)  # 数据集总样本数
    num_batches = len(dataloader)  # 批次数量（多少批）
    # print('num_batches =', num_batches)
    model.eval()
    true_label_list, pred_label_list= [], []

    with torch.no_grad(): # 上下文管理器，将其包裹的代码块中的梯度计算禁用，以减少内存使用和加速计算。
        for X, y in dataloader:
            X, y = X.unsqueeze(1).to(device), y.to(device)  # #将测试数据移动到指定的设备，以确保与模型的设备匹配。
            pred = model(X)
            
            true_label_list.append(y.cpu().detach().numpy())
            pred_label_list.append(pred.argmax(dim=1).cpu().detach().numpy())

    y_true = np.concatenate(true_label_list)
    y_pred = np.concatenate(pred_label_list)
    acc = accuracy_score(y_true,y_pred)
    precision, recall, f1 = precision_recall_fscore_support(y_true, y_pred, average='weighted')[:-1]
    # 还可以增加其他计算指标 mcc，auc等等
    return acc, precision, recall, f1

# 一审
def set_random_seed(seed):
    """设置随机种子确保可重现性"""
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    torch.Generator().manual_seed(seed)  # dataloader的随机种子
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

class LSTMModel(nn.Module):
    def __init__(self, input_size, hidden_size, output_size, num_layers=1):
        super(LSTMModel, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.output_size = output_size
 
        # 定义lsmt层
        # batch_first=True表示输入数据的形状是(batch_size, sequence_length, input_size)
        # 而不是默认的(sequence_length, batch_size, input_size)。
        # batch_size是指每个训练批次中包含的样本数量
        # sequence_length是指输入序列的长度
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
 
        # 定义全连接层，将LSTM层的输出映射到最终的输出空间。
        self.fc = nn.Linear(hidden_size, output_size)

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
        # 初始化了隐藏状态h0和细胞状态c0，并将其设为零向量。
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
 
        # LSTM层前向传播
        # 将输入数据x以及初始化的隐藏状态和细胞状态传入LSTM层
        # 得到输出out和更新后的状态。
        # out的形状为(batch_size, sequence_length, hidden_size)。
        out, _ = self.lstm(x, (h0, c0))
 
        # 全连接层前向传播
        # 使用LSTM层的最后一个时间步的输出out[:, -1, :]（形状为(batch_size, hidden_size)）作为全连接层的输入，得到最终的输出。
        out = self.fc(out[:, -1, :])
        # 一审
        if self.loss_function == "nllloss":
            return F.log_softmax(out, dim=1)
        return out
        # # 整合新加的softmax，crossentropy已经包含了softmax，所以结果不变
        # if (self.output_size == 2):
        #     act = nn.Softmax(dim=1).to(device)
        #     out = act(out)
        # return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--jobID", default="20250415140649_Zefvf3Fa", type=str)
    parser.add_argument("--kfold", default=0, type=int)  # 0 表示不使用kfold
    parser.add_argument("--ratio", default="0", type=str)  # # "0" 表示不使用split，值只能以:分割，e.g. 8:1:1
    parser.add_argument("--epochs", default=5, type=int)
    parser.add_argument("--es", default=100, type=int)
    parser.add_argument("--lr", default=0.001, type=float)
    parser.add_argument("--bs", default=32, type=int, help="batch size")
    parser.add_argument("--loss_function", default="crossentropy", type=str)  # 交叉熵损失函数 crossentropy, nllloss, focalloss
    parser.add_argument("--optimizer_function", default="adam", type=str)  # adam, rmsprop, sgd
    parser.add_argument("--output_size", default=2, type=int)  # 分类数
    parser.add_argument("--type", default="single", type=str)  # all表示运行所有模型，修改result路径；single表示只运行当前模型
    parser.add_argument('--random_seed', type=int, default=42, help='random seed')  # 一审新增


    args = parser.parse_args()
    jobID = args.jobID
    kfold = args.kfold
    ratio = args.ratio
    epochs = args.epochs
    es = args.es
    lr = args.lr
    batch_size = args.bs
    loss_function = args.loss_function
    optimizer_function = args.optimizer_function
    output_size = args.output_size  # 分类数
    type = args.type

    print('jobID =',jobID)
    print('model = LSTM')
    print('kfold =', kfold)
    print('ratio =', ratio)
    print('epochs =', epochs)
    print('earlystopping =', es)
    print('learning rate =', lr)
    print('batch size =', batch_size)
    print('loss function =', loss_function)
    print('optimizer function =', optimizer_function)
    print('label number =', output_size)
    random_seed = args.random_seed  # 一审新增
    print('random seed =', random_seed)  # 一审新增
    set_random_seed(random_seed)  # 一审新增

    hidden_size = 32
    num_layers = 2 # LSTM层数
    # 单层LSTM：适用于简单的序列建模任务，结构简单，计算效率高。
    # 多层LSTM：适用于复杂的序列建模任务，能够捕捉更复杂的模式和长距离依赖，但需要更多的计算资源。
    # 层数选择：需要通过实验来确定，考虑任务复杂度、数据量和计算资源。


    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # savename = 'D:\\wamp\www\\multi_omics_own\\download_data\\Jobs\\'+jobID+'\\result\\model.pt'
    if (type == "all"):
        result_path = '/xp/www/AutoMATA/download_data/Jobs/'+jobID+'/result/lstm/'
    else:
        result_path = '/xp/www/AutoMATA/download_data/Jobs/'+jobID+'/result/'
    
    if not os.path.exists(result_path):
        os.makedirs(result_path)

    savename = result_path+'model.pth'
    early_stopping = EarlyStopping(es, verbose=True, savename=savename, delta=0.0001)

    # 处理数据 需要split
    if (ratio != "0"):
        process(jobID=jobID, ratio=ratio)
    

    # 加载训练数据集
    X_train, Y_train = load_data("train", jobID=jobID)
    # print(X_train)
    # print(Y_train)

    # 自动检测实际类别数量，覆盖命令行参数
    actual_num_classes = len(torch.unique(Y_train))
    if actual_num_classes != output_size:
        print(f"警告：用户设置的类别数 ({output_size}) 与数据实际类别数 ({actual_num_classes}) 不一致")
        print(f"自动使用实际类别数：{actual_num_classes}")
        output_size = actual_num_classes


    '''训练模型'''
    # input_size输入特征的维度
    # hidden_size隐藏层的维度，即每个LSTM单元的隐藏状态向量的维度。
    # output_size：输出的维度。
    # num_layers：LSTM层的数量，默认为1。
    input_size = X_train.shape[1]  # 多少个特征 特征数量

    # 使用Stratifiedkfold几折交叉验证训练模型
    if (kfold):
        kfscore = []
        # https://blog.csdn.net/u013685264/article/details/126488633
        skf = StratifiedKFold(n_splits=kfold)  # 保证每次跑的时候分的数据都是一致的，注意shuffle=False（默认）
        for i, (train_idx, val_idx) in enumerate(skf.split(X_train, Y_train)):
            # print(val_idx)  # 索引
            print("--------The {} fold is training---------".format(i+1))
            # trainset, valset = torch.FloatTensor(np.array(X_train)[[train_idx]]), torch.FloatTensor(np.array(X_train)[[val_idx]])
            # traintag, valtag = torch.LongTensor(np.array(Y_train)[[train_idx]]), torch.LongTensor(np.array(Y_train)[[val_idx]])
            trainset, valset = torch.FloatTensor(np.array(X_train)[train_idx]), torch.FloatTensor(np.array(X_train)[val_idx])
            traintag, valtag = torch.LongTensor(np.array(Y_train)[train_idx]), torch.LongTensor(np.array(Y_train)[val_idx])
            # print(trainset)
            # print(traintag)
            train_dataset = torch.utils.data.TensorDataset(trainset, traintag)
            train_loader = DataLoader(dataset=train_dataset, batch_size=batch_size, shuffle=True)
            val_dataset =  torch.utils.data.TensorDataset(valset, valtag)
            val_loader = DataLoader(dataset=val_dataset, batch_size=batch_size, shuffle=True)

            # define model
            lstm = LSTMModel(input_size, hidden_size, output_size, num_layers).to(device)
            val_acc_s = []  # 存储每个 epoch 的准确率
            val_loss_s = []  # 存储每个 epoch 的损失值
            train_acc_s = []  # 存储每个 epoch 的准确率
            train_loss_s = []  # 存储每个 epoch 的损失值
            for t in range(epochs):
                print("--------Begin the {} epoch training---------".format(t+1))
                # 训练模型
                train_loss, train_acc, train_precision, train_recall, train_f1 = train(dataloader=train_loader, model=lstm)
                # 验证模型
                val_loss, val_acc, val_precision, val_recall, val_f1 = validate(dataloader=val_loader, model=lstm)
                print("train loss = {}, acc = {}, precision = {}, recall = {}, f1 = {} ".format(round(train_loss, 4), round(train_acc, 4), round(train_precision, 4), round(train_recall, 4), round(train_f1, 4)))
                print("validation loss = {}, acc = {}, precision = {}, recall = {}, f1 = {}".format(round(val_loss, 4), round(val_acc, 4), round(val_precision, 4), round(val_recall, 4), round(val_f1, 4)))

                train_acc_s.append(train_acc)
                train_loss_s.append(train_loss)
                val_acc_s.append(val_acc)
                val_loss_s.append(val_loss)

                early_stopping(val_loss, lstm)
                if early_stopping.early_stop:
                    print('early stopping')
                    epochs = t+1  # 保存早停的迭代次数
                    break

            print("--------The {} fold validation result---------".format(i+1))
            val_acc, val_precision, val_recall, val_f1 = test(dataloader=val_loader, model=lstm)
            print("validation acc = {}, precision = {}, recall = {}, f1 = {}".format(round(val_acc, 4), round(val_precision, 4), round(val_recall, 4), round(val_f1, 4)))
            kfscore.append(test(dataloader=val_loader, model=lstm))
        
        # average score
        kfscore = np.array(kfscore).sum(axis= 0)/float(kfold)  # acc, precision, recall, f1
        print("--------KFold Final Average Validation Results---------")
        print("Stratified KFold mean validation acc = {}, precision = {}, recall = {}, f1 = {}".format(round(kfscore[0], 4), round(kfscore[1], 4), round(kfscore[2], 4), round(kfscore[3], 4)))



    else:
        # 不用kfold
        # 加载验证数据集
        lstm = LSTMModel(input_size, hidden_size, output_size, num_layers).to(device)
        train_dataset =  torch.utils.data.TensorDataset(X_train, Y_train)
        train_loader = DataLoader(dataset=train_dataset, batch_size=batch_size, shuffle=True)
        X_val, Y_val = load_data("validate", jobID=jobID)
        val_dataset =  torch.utils.data.TensorDataset(X_val, Y_val)
        val_loader = DataLoader(dataset=val_dataset, batch_size=batch_size, shuffle=True)

        val_acc_s = []  # 存储每个 epoch 的准确率
        val_loss_s = []  # 存储每个 epoch 的损失值
        train_acc_s = []  # 存储每个 epoch 的准确率
        train_loss_s = []  # 存储每个 epoch 的损失值
        for t in range(epochs):
            print("--------Begin the {} epoch training---------".format(t+1))
            # 训练模型
            train_loss, train_acc, train_precision, train_recall, train_f1 = train(dataloader=train_loader, model=lstm)
            # 验证模型
            val_loss, val_acc, val_precision, val_recall, val_f1  = validate(dataloader=val_loader, model=lstm)
            print("train loss = {}, acc = {}, precision = {}, recall = {}, f1 = {} ".format(round(train_loss, 4), round(train_acc, 4), round(train_precision, 4), round(train_recall, 4), round(train_f1, 4)))
            print("validation loss = {}, acc = {}, precision = {}, recall = {}, f1 = {}".format(round(val_loss, 4), round(val_acc, 4), round(val_precision, 4), round(val_recall, 4), round(val_f1, 4)))

            train_acc_s.append(train_acc)
            train_loss_s.append(train_loss)
            val_acc_s.append(val_acc)
            val_loss_s.append(val_loss)

            early_stopping(val_loss, lstm)
            if early_stopping.early_stop:
                print('early stopping')
                epochs = t+1  # 保存早停的迭代次数
                break




    '''保存模型https://blog.csdn.net/chumingqian/article/details/124696856'''
    # with open(savename, 'wb') as outfile:
    #     pickle.dump(lstm, outfile)  
    torch.save({
        'epochs': epochs,
        'model_state_dict': lstm.state_dict(), 
        'loss_function': loss_function,
        'optimizer_function': optimizer_function,
        'output_size': output_size,
        'input_size': input_size,
        'hidden_size': hidden_size,
        'num_layers': num_layers,
        'learning_rate': lr
    }, savename)

    '''加载模型'''
    # with open(savename, 'rb') as infile:
    #     lstm = pickle.load(infile)

    '''绘制训练-验证曲线'''
    # 创建子图，分别用于绘制准确率和损失值
    plt.plot(list(range(1, epochs+1)), train_loss_s, label = 'training loss')  # 测试集loss  acc
    plt.plot(list(range(1, epochs+1)), val_loss_s, label = 'validation loss')  # 验证集损失  val_acc
    plt.plot(list(range(1, epochs+1)), train_acc_s, label = 'training accuracy')  # 测试集loss  acc
    plt.plot(list(range(1, epochs+1)), val_acc_s, label = 'validation accuracy')  # 验证集损失  val_acc

    plt.xlabel("Epoch")  # 坐标轴
    plt.ylabel("Loss—Accuracy")

    plt.title('acc-loss curve')
    plt.legend(loc='upper left')
    # plt.savefig("D:\\wamp\\www\\multi_omics_own\\download_data\\Jobs\\"+jobID+"\\result\\figure"+".png", format='png')
    plt.savefig(result_path + "figure.png", format='png', dpi=300)
    plt.close()

    print("Done!")  # 训练结束


    '''测试模型'''
    # 加载测试数据集
    X_test, Y_test = load_data("test", jobID=jobID)
    test_dataset =  torch.utils.data.TensorDataset(X_test, Y_test)
    test_loader = DataLoader(dataset=test_dataset, batch_size=batch_size, shuffle=True)

    acc, precision, recall, f1 = test(dataloader=test_loader, model=lstm)
    print("test acc = {}, precision = {}, recall = {}, f1 = {}".format(acc, precision, recall, f1))

    # 保存模型测试结果
    # with open("D:\\wamp\\www\\multi_omics_own\\download_data\\Jobs\\"+jobID+"\\result\\"+"test_result.txt", mode="w") as f:
    with open(result_path + "test_result.txt", mode="w") as f:
        f.write("test result: \n")
        f.write("acc = " + str(round(acc, 4)) + "\n")
        f.write("precision = " + str(round(precision, 4)) + "\n")
        f.write("recall = " + str(round(recall, 4)) + "\n")
        f.write("f1 = " + str(round(f1, 4)) + "\n")
