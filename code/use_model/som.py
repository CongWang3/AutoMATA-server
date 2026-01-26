# 使用base
# 参数待改——web提交的参数
# softmax和sigmoid区别：https://blog.csdn.net/orangerfun/article/details/104610725
# https://www.cnblogs.com/ludiboke/p/11758201.html
# https://blog.csdn.net/qq_41994220/article/details/118311605 minisom
# https://blog.csdn.net/weixin_44333889/article/details/118214044  minisom
import shutup  # 控制台输出 忽略 warning
shutup.please()

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




# class SOM(object):
#     def __init__(self, X, output, iteration, batch_size):
#         """
#         :param X:  形状是N*D， 输入样本有N个,每个D维
#         :param output: (n,m)一个元组，为输出层的形状是一个n*m的二维矩阵
#         :param iteration:迭代次数
#         :param batch_size:每次迭代时的样本数量
#         初始化一个权值矩阵，形状为D*(n*m)，即有n*m权值向量，每个D维
#         """
#         self.X = X
#         self.output = output
#         self.iteration = iteration
#         self.batch_size = batch_size
#         self.W = np.random.rand(X.shape[1], output[0] * output[1])
#         print(self.W.shape)

#     def GetN(self, t):
#         """
#         :param t:时间t, 这里用迭代次数来表示时间
#         :return: 返回一个整数，表示拓扑距离，时间越大，拓扑邻域越小
#         """
#         a = min(self.output)
#         return int(a - float(a) * t / self.iteration)

#     def Geteta(self, t, n):
#         """
#         :param t: 时间t, 这里用迭代次数来表示时间
#         :param n: 拓扑距离
#         :return: 返回学习率，
#         """
#         return np.power(np.e, -n) / (t + 2)

#     def updata_W(self, X, t, winner):
#         N = self.GetN(t)
#         for x, i in enumerate(winner):
#             to_update = self.getneighbor(i[0], N)
#             for j in range(N + 1):
#                 e = self.Geteta(t, j)
#                 for w in to_update[j]:
#                     self.W[:, w] = np.add(self.W[:, w], e * (X[x, :] - self.W[:, w]))

#     def getneighbor(self, index, N):
#         """
#         :param index:获胜神经元的下标
#         :param N: 邻域半径
#         :return ans: 返回一个集合列表，分别是不同邻域半径内需要更新的神经元坐标
#         """
#         a, b = self.output
#         length = a * b

#         def distence(index1, index2):
#             i1_a, i1_b = index1 // a, index1 % b
#             i2_a, i2_b = index2 // a, index2 % b
#             return np.abs(i1_a - i2_a), np.abs(i1_b - i2_b)

#         ans = [set() for i in range(N + 1)]
#         for i in range(length):
#             dist_a, dist_b = distence(i, index)
#             if dist_a <= N and dist_b <= N: ans[max(dist_a, dist_b)].add(i)
#         return ans

#     def train(self):
#         """
#         train_Y:训练样本与形状为batch_size*(n*m)
#         winner:一个一维向量，batch_size个获胜神经元的下标
#         :return:返回值是调整后的W
#         """
#         count = 0
#         while self.iteration > count:
#             train_X = self.X[np.random.choice(self.X.shape[0], self.batch_size)]
#             normal_W(self.W)
#             normal_X(train_X)
#             train_Y = train_X.dot(self.W)
#             winner = np.argmax(train_Y, axis=1).tolist()
#             self.updata_W(train_X, count, winner)
#             count += 1
#         return self.W

#     def train_result(self):
#         normal_X(self.X)
#         train_Y = self.X.dot(self.W)
#         winner = np.argmax(train_Y, axis=1).tolist()
#         print(winner)
#         return winner


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



if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--jobID", default="20250416150624_agTW5its", type=str)
    parser.add_argument("--model_type", default="SOM", type=str)
    args = parser.parse_args()
    jobID = args.jobID

    print('jobID =',jobID)
    print('model_type = SOM')

    # 保存模型
    savename = '/xp/www/AutoMATA/download_data/Jobs/'+jobID+'/model.pth'
    savename_2 = '/xp/www/AutoMATA/download_data/Jobs/'+jobID+'/winmap.pkl'
    
    # 加载模型
    with open(savename, 'rb') as infile:
        som = pickle.load(infile)
    with open(savename_2, 'rb') as infile:
        winmap = pickle.load(infile)
        


    # 加载测试数据集
    X_test, Y_test, name = load_data("test", jobID=jobID)
    
    # 进行分类预测
    y_pred = classify(som, X_test, winmap)

    acc = accuracy_score(Y_test, y_pred)
    precision, recall, f1 = precision_recall_fscore_support(Y_test, y_pred, average='macro')[:-1]
    print("test acc = {}, precision = {}, recall = {}, f1 = {}".format(acc, precision, recall, f1))

    '''保存使用本模型测试结果指标'''
    # with open("D:\\wamp\\www\\multi_omics_own\\model\\result\\"+jobID+"_result.txt", mode="w") as f:
    with open("/xp/www/AutoMATA/download_data/Jobs/"+jobID+"/result/test_metrics_result.txt", mode="w") as f:
        f.write("test result: \n")
        f.write("acc = " + str(acc) + "\n")
        f.write("precision = " + str(precision) + "\n")
        f.write("recall = " + str(recall) + "\n")
        f.write("f1 = " + str(f1) + "\n")


    '''保存使用本模型的测试结果'''
    with open("/xp/www/AutoMATA/download_data/Jobs/"+jobID+"/result/test_result.txt", mode="w") as f:
        # f.write("name" + "\t" + "Prediction label" + "\n")
        f.write("name" + "\t" + "probability" + "\n")
        for i in range(len(name)):
            f.write(name[i] + "\t" + str(y_pred[i]) + "\n")



    
    

