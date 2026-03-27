import shutup  # 控制台输出 忽略 warning
shutup.please()

from sklearn.utils import shuffle
from sklearn.preprocessing import LabelEncoder
import torch.optim
import warnings
import pandas as pd
import torch
# import os
# os.environ['CUDA_VISIBLE_DEVICES'] ='0'  # 参数待改



warnings.simplefilter(action='ignore', category=RuntimeWarning)



def load_data(
    state="train",
    jobID="20240808232043_OtJF37SH",
    feature_indices=None,
):  # train, val, test

    if state == "train":
        data = pd.read_csv("/xp/www/AutoMATA/download_data/Jobs/"+jobID+"/"+jobID+"_data.txt", sep="\t")
        # data = pd.read_csv("D:\\wamp\www\\multi_omics_own\\download_data\\Jobs\\"+jobID+"\\"+jobID+"_data.txt", sep="\t")  # train 改为 data，为了train+analysis流程
    elif state == "test":
        data = pd.read_csv("/xp/www/AutoMATA/download_data/Jobs/"+jobID+"/"+jobID+"_test.txt", sep="\t")
        # data = pd.read_csv("D:\\wamp\www\\multi_omics_own\\download_data\\Jobs\\"+jobID+"\\"+jobID+"_test.txt", sep="\t")
    else:  
        data = pd.read_csv("/xp/www/AutoMATA/download_data/Jobs/"+jobID+"/"+jobID+"_val.txt", sep="\t")
        # data = pd.read_csv("D:\\wamp\www\\multi_omics_own\\download_data\\Jobs\\"+jobID+"\\"+jobID+"_val.txt", sep="\t")

    # 获取每条数据的名称 GeneID
    name = data.iloc[:, 0].values.astype(str) 
    # 获取数据
    feature = data.iloc[:, 1:-1].values.astype(float)
    # 如果模型训练时做过特征选择，需要在推理阶段对测试集做同样的子集裁剪
    if feature_indices is not None:
        # feature_indices 可能来自 checkpoint（list/ndarray/torch tensor）
        import numpy as _np
        idx = _np.array(feature_indices, dtype=int).ravel()
        feature = feature[:, idx]
    label = data.iloc[:,-1].values


    encoder = LabelEncoder()
    label = encoder.fit_transform(label.ravel())

    feature, label, name = torch.FloatTensor(feature), torch.LongTensor(label), name
    return feature, label, name
