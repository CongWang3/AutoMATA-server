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
import itertools


import argparse
import pickle


from DataProcess import load_data,process

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

# 可视化
def show(som, output_size, result_path):
    """ 在输出层画标签图案 """
    plt.figure(figsize=(16, 16))
    # 定义不同标签的图案标记
    # markers = ['o', 's', 'D']
    # colors = ['C0', 'C1', 'C2']
    # category_color = {'setosa': 'C0', 'versicolor': 'C1', 'virginica': 'C2'}

    # 二分类
    # markers = ['o', 's']
    # colors = ['C0', 'C1']
    # category_color = {'0': 'C0', '1': 'C1'}
    # 类名
    # class_names = ['0', '1']

    all_markers = ['o', 's', 'D', 'v', 'P', '*', 'X']
    all_colors = ['C0', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6']
    all_category_color = {'0': 'C0', '1': 'C1', '2': 'C2', '3': 'C3', '4': 'C4', '5': 'C5', '6': 'C6'}
    all_class_names = ['0', '1', '2', '3', '4', '5', '6']
    # 多分类
    markers = all_markers[0:output_size] # 'V', 'P', '*', 'X'
    colors = all_colors[0:output_size]
    category_color = dict(itertools.islice(all_category_color.items(), output_size))
    # 类名
    class_names = all_class_names[0:output_size]



    # 背景上画U-Matrix
    heatmap = som.distance_map()
    # 画背景图
    plt.pcolor(heatmap, cmap='bone_r')

    for cnt, xx in enumerate(X_train):
        w = som.winner(xx)
        # 在样本Heat的地方画上标记
        plt.plot(w[0] + .5, w[1] + .5, markers[Y_train[cnt]], markerfacecolor='None',
                 markeredgecolor=colors[Y_train[cnt]], markersize=12, markeredgewidth=2)

    plt.axis([0, size, 0, size])
    ax = plt.gca()
    # 颠倒y轴方向
    ax.invert_yaxis()
    legend_elements = [Patch(facecolor=clr, edgecolor='w', label=l) for l, clr in category_color.items()]
    plt.legend(handles=legend_elements, loc='center left', bbox_to_anchor=(1, .95))
    # plt.show()
    # plt.savefig("D:\\wamp\\www\\multi_omics_own\\download_data\\Jobs\\"+jobID+"\\result\\figure"+"_1.png", format='png')
    plt.savefig(result_path + "figure.png", format='png', dpi=300)
    plt.close()

    """ 在每个格子里画饼图，且用颜色表示类别，用数字表示总样本数量 """
    

    # plt.figure(figsize=(16, 16))
    # the_grid = GridSpec(size, size)
    # plt.title('classify figure')

    # for position in winmap.keys():
    #     label_fracs = [winmap[position][label] for label in [0, 1]]  # [0, 1, 2]
    #     plt.subplot(the_grid[position[1], position[0]], aspect=1)
    #     # print('label_fracs =', label_fracs)
    #     patches, texts = plt.pie(label_fracs)
    #     # print('patches =', patches)
    #     plt.text(position[0] / 100, position[1] / 100, str(len(list(winmap[position].elements()))),
    #              color='black', fontdict={'weight': 'bold', 'size': 15}, va='center', ha='center')
        
    # plt.legend(patches, class_names, loc='center right', bbox_to_anchor=(-1, 9), ncol=2)  # 没有label啊！！！！
    # # plt.savefig("D:\\wamp\\www\\multi_omics_own\\download_data\\Jobs\\"+jobID+"\\result\\figure"+"_2.png", format='png')
    # plt.savefig(result_path + "figure_2.png", format='png', dpi=300)

    # plt.close()
    # plt.show()


if __name__ == '__main__':
    
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
    parser.add_argument('--feature_method', type=str, default=None, help='Feature selection method: PCC, SPEARMAN, CHI2, RF, etc.')


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
    feature_method = args.feature_method if args.feature_method and args.feature_method.strip() else None

    print('jobID =',jobID)
    print('model = SOM')
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
    print('feature selection method =', feature_method if feature_method else 'none')
    set_random_seed(random_seed)  # 一审新增



    # 处理数据 需要split
    if (ratio != "0"):
        process(jobID=jobID, ratio=ratio)
    
    
    iterations = epochs
    # 使用 Stratifiedkfold 几折交叉验证训练模型
    if (kfold):
        kfscore = []
        # https://blog.csdn.net/u013685264/article/details/126488633
        skf = StratifiedKFold(n_splits=kfold)  # 保证每次跑的时候分的数据都是一致的，注意 shuffle=False（默认）
        # 加载数据集
        X_train_total, Y_train_total, feature_indices = load_data("train", jobID=jobID, feature_method=feature_method)
            
        # 自动检测实际类别数量，覆盖命令行参数
        actual_num_classes = len(torch.unique(torch.LongTensor(Y_train_total)))
        if actual_num_classes != output_size:
            # print(f"警告：用户设置的类别数 ({output_size}) 与数据实际类别数 ({actual_num_classes}) 不一致")
            # print(f"自动使用实际类别数：{actual_num_classes}")
            print(f"Warning: The number of classes set by the user ({output_size}) does not match the actual number of classes in the data ({actual_num_classes})")
            print(f"Automatically use the actual number of classes: {actual_num_classes}")
            output_size = actual_num_classes

        for i, (train_idx, val_idx) in enumerate(skf.split(X_train_total, Y_train_total)):
            print("--------The {} fold is training---------".format(i+1))
            X_train, X_val = np.array(X_train_total)[train_idx], np.array(X_train_total)[val_idx]
            Y_train, Y_val = np.array(Y_train_total)[train_idx], np.array(Y_train_total)[val_idx]
            # 样本数量
            N = X_train.shape[0]
            # 维度/特征数量
            M = X_train.shape[1]
            # 经验公式：决定输出层尺寸
            size = math.ceil(np.sqrt(5 * np.sqrt(N)))
            # print("训练样本个数:{}  验证样本个数:{}".format(N, X_val.shape[0]))
            # print("输出网格最佳边长为:", size)
            print("The best side length of the grid is :", size)

            # 初始化模型
            som = MiniSom(size, size, M, sigma=3, learning_rate=lr, neighborhood_function='bubble')
            # 初始化权值
            try:
                som.pca_weights_init(X_train)
            except ValueError as e:
                # MiniSom 的 pca 初始化要求特征维度至少 2；当特征选择导致剩余维度不足时自动回退。
                print(f"[SOM] pca_weights_init failed ({e}); fallback to random_weights_init.")
                som.random_weights_init(X_train)
            # 模型训练
            som.train_batch(X_train, iterations, verbose=False)

            # 利用标签信息，标注训练好的som网络
            winmap = som.labels_map(X_train, Y_train)
            
            print("Finish training!")  # 训练结束

            # 进行分类预测
            print("--------The {} fold validation result---------".format(i+1))
            y_pred = classify(som, X_val, winmap)
            acc = accuracy_score(Y_val, y_pred)
            precision, recall, f1 = precision_recall_fscore_support(Y_val, y_pred, average='weighted')[:-1]
            print("validation acc = {}, precision = {}, recall = {}, f1 = {}".format(round(acc,4), round(precision,4), round(recall,4), round(f1,4)))
            kfscore.append([acc, precision, recall, f1])
        
        # average score
        kfscore = np.array(kfscore).sum(axis= 0)/float(kfold)  # acc, precision, recall, f1
        print("--------KFold Final Average Validation Results---------")
        print("Stratified KFold mean validation acc = {}, precision = {}, recall = {}, f1 = {}".format(round(kfscore[0], 4), round(kfscore[1], 4), round(kfscore[2], 4), round(kfscore[3], 4)))

    else:
        # 不用 kfold
        # 加载训练数据集
        X_train, Y_train, feature_indices = load_data("train", jobID=jobID, feature_method=feature_method)
            
        # 自动检测实际类别数量，覆盖命令行参数
        actual_num_classes = len(torch.unique(torch.LongTensor(Y_train)))
        if actual_num_classes != output_size:
            print(f"警告：用户设置的类别数 ({output_size}) 与数据实际类别数 ({actual_num_classes}) 不一致")
            print(f"自动使用实际类别数：{actual_num_classes}")
            output_size = actual_num_classes
            
        X_train, Y_train = np.array(X_train), np.array(Y_train)
        X_val, Y_val, _ = load_data("validate", jobID=jobID, feature_indices=feature_indices)
        X_val, Y_val = np.array(X_val), np.array(Y_val)
        # 样本数量
        N = X_train.shape[0]
        # 维度/特征数量
        M = X_train.shape[1]
        # 经验公式：决定输出层尺寸
        size = math.ceil(np.sqrt(5 * np.sqrt(N)))
        # print("训练样本个数:{}  验证样本个数:{}".format(N, X_val.shape[0]))
        # print("网格最佳边长为:", size)
        print("The best side length of the grid is :", size)


        # 初始化模型
        som = MiniSom(size, size, M, sigma=3, learning_rate=lr, neighborhood_function='bubble')
        # 初始化权值
        try:
            som.pca_weights_init(X_train)
        except ValueError as e:
            # MiniSom 的 pca 初始化要求特征维度至少 2；当特征选择导致剩余维度不足时自动回退。
            print(f"[SOM] pca_weights_init failed ({e}); fallback to random_weights_init.")
            som.random_weights_init(X_train)
        # 模型训练
        som.train_batch(X_train, iterations, verbose=False)

        # 利用标签信息，标注训练好的som网络
        winmap = som.labels_map(X_train, Y_train)
        
        print("Finish training!")  # 训练结束

        # 进行分类预测
        y_pred = classify(som, X_val, winmap)

        acc = accuracy_score(Y_val, y_pred)
        precision, recall, f1 = precision_recall_fscore_support(Y_val, y_pred, average='weighted')[:-1]
        print("validation acc = {}, precision = {}, recall = {}, f1 = {}".format(round(acc,4), round(precision,4), round(recall,4), round(f1,4)))


    if feature_indices is not None:
        print("selected feature indices (1-based):", feature_indices + 1)
    else:
        print("feature selection: none (all features)")

    print("Done!")  # 训练结束

    

    # 保存模型
    if (type == "all"):
        result_path = str(path_jobs() / jobID / "result" / "som") + "/"
    else:
        result_path = str(path_jobs() / jobID / "result") + "/"

    if not os.path.exists(result_path):
        os.makedirs(result_path)
        
    savename = result_path+'model.pth'
    # savename_2 = result_path+'winmap.pkl'

    # with open(savename_2, 'wb') as outfile:
    #     pickle.dump(winmap, outfile)
    # with open(savename, 'wb') as outfile:
    #     pickle.dump(som, outfile)
    checkpoint = {
        'som': som,
        'winmap': winmap,
        'feature_indices': feature_indices,
        'output_size': output_size,
        'learning_rate': lr,
        'epochs': epochs,
        'kfold': kfold,
        'batch_size': batch_size,
    }
    torch.save(checkpoint, savename)

    # torch.save({
    #     'epochs': epochs,
    #     'model_state_dict': som.state_dict(), 
    #     'loss_function': loss_function,
    #     'optimizer_function': optimizer_function,
    #     'size': size,
    #     'M': M,
    #     'sigma': sigma,
    #     'neighborhood_function': 'bubble',
    #     'learning_rate': lr
    # }, savename)

    # 可视化
    show(som, output_size, result_path)
    

    # 加载测试数据集
    X_test, Y_test, _ = load_data("test", jobID=jobID, feature_indices=feature_indices)
    
    # 进行分类预测
    y_pred = classify(som, X_test, winmap)

    acc = accuracy_score(Y_test,y_pred)
    precision, recall, f1 = precision_recall_fscore_support(Y_test, y_pred, average='weighted')[:-1]
    print("test acc = {}, precision = {}, recall = {}, f1 = {}".format(round(acc,4), round(precision,4), round(recall,4), round(f1,4)))


    # 保存模型测试结果
    # with open("D:\\wamp\\www\\multi_omics_own\\download_data\\Jobs\\"+jobID+"\\result\\"+"test_result.txt", mode="w") as f:
    with open(result_path + "test_result.txt", mode="w") as f:
        f.write("test result: \n")
        f.write("acc = " + str(round(acc, 4)) + "\n")
        f.write("precision = " + str(round(precision, 4)) + "\n")
        f.write("recall = " + str(round(recall, 4)) + "\n")
        f.write("f1 = " + str(round(f1, 4)) + "\n")

    # 展示在测试集上的效果
    print('test set result')
    print(classification_report(Y_test, np.array(y_pred)))  # 真实label

    
    

