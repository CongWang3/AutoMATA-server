# 使用base
# 参数待改——web提交的参数
# softmax和sigmoid区别：https://blog.csdn.net/orangerfun/article/details/104610725
# https://www.cnblogs.com/ludiboke/p/11758201.html
# https://blog.csdn.net/qq_41994220/article/details/118311605 minisom
# https://blog.csdn.net/weixin_44333889/article/details/118214044  minisom
import shutup  # 控制台输出 忽略 warning
shutup.please()

import sys
from pathlib import Path
_code_dir = Path(__file__).resolve().parents[1]
if str(_code_dir) not in sys.path:
    sys.path.insert(0, str(_code_dir))
from automata_paths import path_jobs

"""
Much of the code is modified from:
- https://codesachin.wordpress.com/2015/11/28/self-organizing-maps-with-googles-tensorflow/
"""

import numpy as np
# from som import SOM
from torch.autograd import Variable
import matplotlib.pyplot as plt

import torch
import torch.nn as nn
import numpy as np
from torch.autograd import Variable
import os
os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"

import numpy as np
import pylab as pl

import math
import numpy as np
# from minisom import MiniSom
from utils.minisom import MiniSom
from sklearn import datasets
from numpy import sum as npsum
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.gridspec import GridSpec

import pandas as pd
from sklearn.utils import shuffle
from sklearn.preprocessing import LabelEncoder
import pickle
from sklearn.metrics import accuracy_score,recall_score,precision_score,f1_score,matthews_corrcoef,confusion_matrix,roc_auc_score,classification_report,multilabel_confusion_matrix,hamming_loss
from sklearn.metrics import precision_recall_fscore_support
from sklearn.model_selection import  StratifiedKFold

# 最后保存两个图
# "D:\\wamp\\www\\multi_omics_own\\model\\figure\\"+jobID+"_2.png", format='png'
# "D:\\wamp\\www\\multi_omics_own\\model\\figure\\"+jobID+".png", format='png'


import argparse
import pickle

from DataProcess import load_data




def normal_X(X):
    """
    :param X:二维矩阵，N*D，N个D维的数据
    :return: 将X归一化的结果
    """
    N, D = X.shape
    for i in range(N):
        temp = np.sum(np.multiply(X[i], X[i]))
        X[i] /= np.sqrt(temp)
    return X


def normal_W(W):
    """
    :param W:二维矩阵，D*(n*m)，D个n*m维的数据
    :return: 将W归一化的结果
    """
    for i in range(W.shape[1]):
        temp = np.sum(np.multiply(W[:, i], W[:, i]))
        W[:, i] /= np.sqrt(temp)
    return W


# 画图
def draw(C):
    colValue = ['r', 'y', 'g', 'b', 'c', 'k', 'm']
    for i in range(len(C)):
        coo_X = []  # x坐标列表
        coo_Y = []  # y坐标列表
        for j in range(len(C[i])):
            coo_X.append(C[i][j][0])
            coo_Y.append(C[i][j][1])
        pl.scatter(coo_X, coo_Y, marker='x', color=colValue[i % len(colValue)], label=i)

    pl.legend(loc='upper right')
    pl.show()




# 分类函数
def classify(som,data,winmap):
    default_class = npsum(list(winmap.values())).most_common()[0][0]
    result = []
    for d in data:
        win_position = som.winner(d)
        if win_position in winmap:
            result.append(winmap[win_position].most_common()[0][0])
        else:
            result.append(default_class)
    return result

def load_checkpoint_compat(path, map_location=None):
    """
    兼容 PyTorch 2.6+：
    torch.load 默认 weights_only=True，会导致旧 checkpoint 反序列化失败。
    这里显式使用 weights_only=False（仅用于受信任的本地训练产物）。
    """
    try:
        return torch.load(path, map_location=map_location, weights_only=False)
    except TypeError:
        # 兼容旧版 PyTorch（无 weights_only 参数）
        return torch.load(path, map_location=map_location)

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--jobID", default="20250416150624_agTW5its", type=str)
    parser.add_argument("--model_type", default="SOM", type=str)
    args = parser.parse_args()
    jobID = args.jobID

    print('jobID =',jobID)
    print('model_type = SOM')
    savename = str(path_jobs() / jobID / "model.pth")

    # 保存模型
    # savename = '/xp/www/AutoMATA/download_data/Jobs/'+jobID+'/model.pth'
    # savename_2 = '/xp/www/AutoMATA/download_data/Jobs/'+jobID+'/winmap.pkl'
    
    # 加载模型
    # with open(savename, 'rb') as infile:
    #     som = pickle.load(infile)
    # with open(savename_2, 'rb') as infile:
    #     winmap = pickle.load(infile)
    # checkpoint = torch.load(savename, map_location="cpu")
    checkpoint = load_checkpoint_compat(savename, map_location="cpu")
    som = checkpoint['som']
    winmap = checkpoint['winmap']
    feature_indices = checkpoint.get('feature_indices', None)

    # load data（若 feature_indices 不为 None，则对测试样本做相同的特征子集选择）
    X_test, Y_test, name = load_data("test", jobID=jobID, feature_indices=feature_indices)
    # X_test, Y_test, name = load_data("test", jobID=jobID)
    
    # 进行分类预测
    y_pred = classify(som, X_test, winmap)

    acc = accuracy_score(Y_test, y_pred)
    precision, recall, f1 = precision_recall_fscore_support(Y_test, y_pred, average='macro')[:-1]
    print("test acc = {}, precision = {}, recall = {}, f1 = {}".format(acc, precision, recall, f1))

    '''保存使用本模型测试结果指标'''
    # with open("D:\\wamp\\www\\multi_omics_own\\model\\result\\"+jobID+"_result.txt", mode="w") as f:
    with open(str(path_jobs() / jobID / "result" / "test_metrics_result.txt"), mode="w") as f:
        f.write("test result: \n")
        f.write("acc = " + str(acc) + "\n")
        f.write("precision = " + str(precision) + "\n")
        f.write("recall = " + str(recall) + "\n")
        f.write("f1 = " + str(f1) + "\n")


    '''保存使用本模型的测试结果'''
    with open(str(path_jobs() / jobID / "result" / "test_result.txt"), mode="w") as f:
        # f.write("name" + "\t" + "Prediction label" + "\n")
        f.write("name" + "\t" + "probability" + "\n")
        for i in range(len(name)):
            f.write(name[i] + "\t" + str(y_pred[i]) + "\n")



    
    

