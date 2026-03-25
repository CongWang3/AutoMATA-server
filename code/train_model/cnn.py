# 使用pt36
# 参数待改——web提交的参数
# 多分类 https://www.cnblogs.com/xiximayou/p/14773460.html
import shutup  # 控制台输出 忽略 warning
shutup.please()

import math
import warnings
import numpy as np
import torch.optim
import torchvision
from torch.utils.data import DataLoader, SubsetRandomSampler
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
from utils.regularization import apply_regularization_loss, apply_max_norm_constraint, create_optimizer_with_reg

warnings.simplefilter(action='ignore', category=RuntimeWarning)
torch.manual_seed(2022)

# 把训练过程print的结果放在log文件中：20240808232043_OtJF37SH.log，用户可以下载训练结果文件, 自己获取最后一轮或者平均训练和验证结果吧

import argparse
import pickle


from DataProcess import load_data,process


def train(dataloader, model):
    model.train()
    num_batches = len(dataloader)
    train_loss= 0 # 积累训练损失
    true_label_list, pred_label_list= [], []

    for data in dataloader:
        X_data, Y_data = data[0].to(device), data[1].to(device)  # 把训练数据集和标签传入cpu或GPU
        output = model(X_data)  # 自动初始化 w权值
        loss = model.criterion(output, Y_data)  # label.squeeze().long() # 通过交叉熵损失函数计算损失值loss
        loss = apply_regularization_loss(loss, model, model.r_method, model.r_weight)

        train_loss += loss.item()  # 计算损失
        true_label_list.append(Y_data.cpu().detach().numpy())
        pred_label_list.append(output.argmax(dim=1).cpu().detach().numpy())
        # Backpropagation 进来一个batch的数据，计算一次梯度，更新一次网络
        model.optimier.zero_grad()  # 梯度值清零
        loss.backward()  # 反向传播计算得到每个参数的梯度值
        model.optimier.step()  # 根据梯度更新网络参数
        if model.r_method == "maxnorm":
            apply_max_norm_constraint(model, model.r_weight)

    y_true = np.concatenate(true_label_list)
    y_pred = np.concatenate(pred_label_list)
    train_loss /= num_batches  # 计算平均损失（一次迭代的损失）
    train_acc = accuracy_score(y_true,y_pred)
    # 总的来说， 如果你的类别比较均衡，则随便； 如果你认为大样本的类别应该占据更重要的位置， 使用Micro； 如果你认为小样本也应该占据重要的位置，则使用 Macro
    # 为了解决 Macro 无法衡量样本均衡问题，一个很好的方法是求加权的 Macro， 因此 Weighed F1 出现了
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
            X, y = X.to(device), y.to(device)  # #将测试数据移动到指定的设备，以确保与模型的设备匹配。
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
            X, y = X.to(device), y.to(device)  # #将测试数据移动到指定的设备，以确保与模型的设备匹配。
            pred = model(X)
            
            true_label_list.append(y.cpu().detach().numpy())
            pred_label_list.append(pred.argmax(dim=1).cpu().detach().numpy())

    y_true = np.concatenate(true_label_list)
    y_pred = np.concatenate(pred_label_list)
    acc = accuracy_score(y_true,y_pred)
    precision, recall, f1 = precision_recall_fscore_support(y_true, y_pred, average='weighted')[:-1]
    # 还可以增加其他计算指标 mcc，auc等等
    return acc, precision, recall, f1

class Cnn(nn.Module):
    def __init__(self, conv_size_1, conv_size_2, output_size, dropout_rate, lr, loss_function, optimizer_function, r_method=None, r_weight=0.0):
        super(Cnn, self).__init__()
        self.output_size = output_size  # 记录flatten层的输出维度——分类数
        self.r_method = r_method
        self.r_weight = r_weight

        self.model1 = nn.Sequential(
            nn.Conv1d(1, conv_size_1, 2, stride=2, padding=6),  # nn.Conv1d(in_channels, out_channels, kernel_size
            nn.ReLU(),
            nn.MaxPool1d(2),  # torch.Size([34, 16, 31])
        )

        self.model2 = nn.Sequential(
            nn.Conv1d(conv_size_1, conv_size_2, 2, padding=6),
            nn.ReLU(),
            nn.MaxPool1d(4),  # torch.Size([34, 32, 7])
            nn.Flatten(),  #torch.Size([34, 224])    (假如上一步的结果为[128, 32, 2]， 那么铺平之后就是[128, 64])
            nn.Dropout(dropout_rate)  # 防止过拟合. dropout_rate=0没作用
        )
        
        self.learning_rate = lr
        self.fc = nn.LazyLinear(self.output_size)  # 一审
        self.loss_function = loss_function  # 一审
        if loss_function == "crossentropy":
            self.criterion = nn.CrossEntropyLoss()
        elif loss_function == "focalloss":
            self.criterion = FocalLoss(gamma=2, alpha=0.25, task_type='multi-class', num_classes=output_size)
        elif loss_function == "nllloss":
            self.criterion = nn.NLLLoss()

        self.optimier = create_optimizer_with_reg(self, optimizer_function, lr, r_method, r_weight)

    def forward(self, input):
        # print(cnn)
        # print('input_1 shape =', input.shape)  # torch.Size([34, 4])
        input = input.reshape(-1,1,input.shape[1])   #结果为torch.Size([34, 1, 4])  目的是把二维变为三维数据
        # print('input_2 shape =', input.shape)
        x = self.model1(input)
        # print('x_1 model1 shape =', x.shape)  # torch.Size([34, 224])
        x = self.model2(x)
        # print('x_2 model1 shape =', x.shape)  # torch.Size([34, 224])
        # fc = nn.Linear(in_features=x.shape[1], out_features=self.output_size, bias=True).to(device)
        # x = fc(x)
        # if (self.output_size == 2):
        #     act = nn.Softmax(dim=1).to(device)
        #     x = act(x)
        # return x
        # 一审
        logits = self.fc(x)
        if self.loss_function == "nllloss":
            return nn.functional.log_softmax(logits, dim=1)
        return logits

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
    parser.add_argument('--random_seed', type=int, default=42, help='随机种子')  # 一审新增
    parser.add_argument('--r_method', type=str, default=None, help='Regularization method: l1, l2, maxnorm, sparsity, or none')
    parser.add_argument('--r_weight', type=float, default=0.0, help='Regularization weight/strength')
    parser.add_argument('--dropout_rate', type=float, default=0.0, help='Dropout rate')
    parser.add_argument('--feature_method', type=str, default=None, help='Feature selection method: PCC, SPEARMAN, CHI2, RF.')

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
    random_seed = args.random_seed  # 一审新增
    r_method = args.r_method if args.r_method and args.r_method != "none" else None
    r_weight = args.r_weight
    dropout_rate = args.dropout_rate
    feature_method = args.feature_method if args.feature_method and args.feature_method.strip() else None

    print('jobID =',jobID)
    print('model = CNN')
    print('kfold =', kfold)
    print('ratio =', ratio)
    print('epochs =', epochs)
    print('earlystopping =', es)
    print('learning rate =', lr)
    print('batch size =', batch_size)
    print('loss function =', loss_function)
    print('optimizer function =', optimizer_function)
    print('label number =', output_size)
    print('random seed =', random_seed)  # 一审新增
    print('regularization method =', r_method if r_method else 'none')
    print('regularization weight =', r_weight)
    print('dropout rate =', dropout_rate)
    print('feature selection method =', feature_method if feature_method else 'none')

    conv_size_1 = 64
    conv_size_2 = 32

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    set_random_seed(random_seed)  # 一审新增

    if (type == "all"):
        result_path = '/xp/www/AutoMATA/download_data/Jobs/'+jobID+'/result/cnn/'
    else:
        result_path = '/xp/www/AutoMATA/download_data/Jobs/'+jobID+'/result/'
    
    if not os.path.exists(result_path):
        os.makedirs(result_path)

    savename = result_path + 'model.pth'
    early_stopping = EarlyStopping(es, verbose=True, savename=savename, delta=0.0001)

    # 处理数据 需要split
    if (ratio != "0"):
        process(jobID=jobID, ratio=ratio)
    

    # 加载训练数据集（可选特征选择）
    X_train, Y_train, feature_indices = load_data("train", jobID=jobID, feature_method=feature_method)
    input_size = X_train.shape[1]
    
    # 自动检测实际类别数量，覆盖命令行参数
    actual_num_classes = len(torch.unique(Y_train))
    if actual_num_classes != output_size:
        print(f"警告: 用户设置的类别数 ({output_size}) 与数据实际类别数 ({actual_num_classes}) 不一致")
        print(f"自动使用实际类别数: {actual_num_classes}")
        output_size = actual_num_classes



    '''训练模型'''

    # 使用Stratifiedkfold几折交叉验证训练模型
    if (kfold):
        kfscore = []
        # https://blog.csdn.net/u013685264/article/details/126488633
        skf = StratifiedKFold(n_splits=kfold)  # 保证每次跑的时候分的数据都是一致的，注意shuffle=False（默认）
        for i, (train_idx, val_idx) in enumerate(skf.split(X_train, Y_train)):
            early_stopping = EarlyStopping(es, verbose=True, savename=savename, delta=0.0001)  # 每个fold要新开一个早停
            print("--------The {} fold is training---------".format(i+1))
            trainset, valset = torch.FloatTensor(np.array(X_train)[train_idx]), torch.FloatTensor(np.array(X_train)[val_idx])
            traintag, valtag = torch.LongTensor(np.array(Y_train)[train_idx]), torch.LongTensor(np.array(Y_train)[val_idx])
            # print(trainset)
            # print(traintag)
            train_dataset = torch.utils.data.TensorDataset(trainset, traintag)
            train_loader = DataLoader(dataset=train_dataset, batch_size=batch_size, shuffle=True)
            val_dataset =  torch.utils.data.TensorDataset(valset, valtag)
            val_loader = DataLoader(dataset=val_dataset, batch_size=batch_size, shuffle=True)

            # define model
            cnn = Cnn(conv_size_1, conv_size_2, output_size, dropout_rate, lr, loss_function, optimizer_function, r_method, r_weight).to(device)
            val_acc_s = []  # 存储每个 epoch 的准确率
            val_loss_s = []  # 存储每个 epoch 的损失值
            train_acc_s = []  # 存储每个 epoch 的准确率
            train_loss_s = []  # 存储每个 epoch 的损失值
            for t in range(epochs):
                print("--------Begin the {} epoch training---------".format(t+1))
                # 训练模型
                train_loss, train_acc, train_precision, train_recall, train_f1 = train(dataloader=train_loader, model=cnn)
                # 验证模型
                val_loss, val_acc, val_precision, val_recall, val_f1 = validate(dataloader=val_loader, model=cnn)
                
                print("train loss = {}, acc = {}, precision = {}, recall = {}, f1 = {} ".format(round(train_loss, 4), round(train_acc, 4), round(train_precision, 4), round(train_recall, 4), round(train_f1, 4)))
                print("validation loss = {}, acc = {}, precision = {}, recall = {}, f1 = {}".format(round(val_loss, 4), round(val_acc, 4), round(val_precision, 4), round(val_recall, 4), round(val_f1, 4)))

                train_acc_s.append(train_acc)
                train_loss_s.append(train_loss)
                val_acc_s.append(val_acc)
                val_loss_s.append(val_loss)

                early_stopping(val_loss, cnn)
                if early_stopping.early_stop:
                    print('early stopping')
                    epochs = t+1  # 保存早停的迭代次数
                    break

            print("--------The {} fold validation result---------".format(i+1))
            val_acc, val_precision, val_recall, val_f1 = test(dataloader=val_loader, model=cnn)
            print("validation acc = {}, precision = {}, recall = {}, f1 = {}".format(round(val_acc, 4), round(val_precision, 4), round(val_recall, 4), round(val_f1, 4)))
            kfscore.append(test(dataloader=val_loader, model=cnn))
        
        # average score
        kfscore = np.array(kfscore).sum(axis= 0)/float(kfold)  # acc, precision, recall, f1
        print("--------KFold Final Average Validation Results---------")
        print("Stratified KFold mean validation acc = {}, precision = {}, recall = {}, f1 = {}".format(round(kfscore[0], 4), round(kfscore[1], 4), round(kfscore[2], 4), round(kfscore[3], 4)))



    else:
        # 不用kfold
        # 加载验证数据集
        cnn = Cnn(conv_size_1, conv_size_2, output_size, dropout_rate, lr, loss_function, optimizer_function, r_method, r_weight).to(device)
        train_dataset =  torch.utils.data.TensorDataset(X_train, Y_train)
        train_loader = DataLoader(dataset=train_dataset, batch_size=batch_size, shuffle=True)
        X_val, Y_val, _ = load_data("validate", jobID=jobID, feature_indices=feature_indices)
        val_dataset =  torch.utils.data.TensorDataset(X_val, Y_val)
        val_loader = DataLoader(dataset=val_dataset, batch_size=batch_size, shuffle=True)

        val_acc_s = []  # 存储每个 epoch 的准确率
        val_loss_s = []  # 存储每个 epoch 的损失值
        train_acc_s = []  # 存储每个 epoch 的准确率
        train_loss_s = []  # 存储每个 epoch 的损失值
        for t in range(epochs):
            print("--------Begin the {} epoch training---------".format(t+1))
            # 训练模型
            train_loss, train_acc, train_precision, train_recall, train_f1 = train(dataloader=train_loader, model=cnn)
            # 验证模型
            val_loss, val_acc, val_precision, val_recall, val_f1  = validate(dataloader=val_loader, model=cnn)
            print("train loss = {}, acc = {}, precision = {}, recall = {}, f1 = {} ".format(round(train_loss, 4), round(train_acc, 4), round(train_precision, 4), round(train_recall, 4), round(train_f1, 4)))
            print("validation loss = {}, acc = {}, precision = {}, recall = {}, f1 = {}".format(round(val_loss, 4), round(val_acc, 4), round(val_precision, 4), round(val_recall, 4), round(val_f1, 4)))

            train_acc_s.append(train_acc)
            train_loss_s.append(train_loss)
            val_acc_s.append(val_acc)
            val_loss_s.append(val_loss)

            early_stopping(val_loss, cnn)
            if early_stopping.early_stop:
                print('early stopping')
                epochs = t+1  # 保存早停的迭代次数
                break

        # exit()




    '''保存模型https://blog.csdn.net/chumingqian/article/details/124696856'''
    # with open(savename, 'wb') as outfile:
    #     pickle.dump(cnn, outfile)
    # torch.save(cnn.state_dict(), 'D:\\wamp\www\\multi_omics_own\\model\\TrainModel\\'+jobID+'.pt')
    torch.save({
        'epochs': epochs,
        'model_state_dict': cnn.state_dict(), 
        'loss_function': loss_function,
        'optimizer_function': optimizer_function,
        'output_size': output_size,
        'conv_size_1': conv_size_1,
        'conv_size_2': conv_size_2,
        'dropout_rate': dropout_rate,
        'learning_rate': lr,
        'input_size': input_size,
        'r_method': r_method,
        'r_weight': r_weight,
        'feature_indices': feature_indices,
    }, savename)


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
    # plt.savefig("D:\\wamp\\www\\multi_omics_own\\download_data\\Jobs\\figure\\"+jobID+".png", format='png')
    # plt.savefig("D:\\wamp\\www\\multi_omics_own\\download_data\\Jobs\\"+jobID+"\\result\\figure"+".png", format='png')
    plt.savefig(result_path + "figure.png", format='png', dpi=300)
    plt.close()

    print("Done!")  # 训练结束


    '''测试模型'''
    # 加载测试数据集
    X_test, Y_test, _ = load_data("test", jobID=jobID, feature_indices=feature_indices)
    test_dataset =  torch.utils.data.TensorDataset(X_test, Y_test)
    test_loader = DataLoader(dataset=test_dataset, batch_size=batch_size, shuffle=True)

    acc, precision, recall, f1 = test(dataloader=test_loader, model=cnn)
    print("test acc = {}, precision = {}, recall = {}, f1 = {}".format(acc, precision, recall, f1))

    # 保存模型测试结果
    # with open("D:\\wamp\\www\\multi_omics_own\\model\\result\\"+jobID+"_result.txt", mode="w") as f:
    with open(result_path + "test_result.txt", mode="w") as f:
        f.write("test result: \n")
        f.write("acc = " + str(round(acc, 4)) + "\n")
        f.write("precision = " + str(round(precision, 4)) + "\n")
        f.write("recall = " + str(round(recall, 4)) + "\n")
        f.write("f1 = " + str(round(f1, 4)) + "\n")